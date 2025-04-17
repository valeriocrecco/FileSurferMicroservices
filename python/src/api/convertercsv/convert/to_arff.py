import pika, json, tempfile, os
import pandas as pd
from bson.objectid import ObjectId
import csv

def csv_2_arff(fileToRead, fileToWrite, relation):
    dataType = [] # Stores data types 'nominal' and 'numeric'
    columnsTemp = [] # Temporary stores each column of csv file except the attributes
    uniqueTemp = [] # Temporary Stores each data cell unique of each column
    uniqueOfColumn = [] # Stores each data cell unique of each column
    dataTypeTemp = [] # Temporary stores the data type for cells on each column
    finalDataType = [] # Finally stores data types 'nominal' and 'numeric'
    attTypes = [] # Stores data type 'numeric' and nominal data for attributes
    p = 0 # pointer for each cell of csv file

    writeFile = open(fileToWrite, 'w')

    #Opening and Reading a CSV file
    f = open(fileToRead, 'r')
    reader = csv.reader(f)
    allData = list(reader)
    attributes = allData[0]
    totalCols = len(attributes)
    totalRows = len(allData)
    f.close()

    # Add a '0' for each empty cell
    for j in range(0,totalCols):
        for i in range(0,totalRows):
            if 0 == len(allData[i][j]):
                allData[i][j] = "0"

    # check for comams or blanks and adds single quotes
    for j in range(0,totalCols):
        for i in range(1,totalRows):
            allData[i][j] = allData[i][j].lower()
            if "\r" in allData[i][j] or '\r' in allData[i][j] or "\n" in allData[i][j] or '\n' in allData[i][j]:
                allData[i][j] = allData[i][j].rstrip(os.linesep)
                allData[i][j] = allData[i][j].rstrip("\n")
                allData[i][j] = allData[i][j].rstrip("\r")
            try:
                if allData[i][j] == str(float(allData[i][j])) or allData[i][j] == str(int(allData[i][j])):
                    print
            except ValueError as e:
                    allData[i][j] = "'" + allData[i][j] + "'"

    # fin gives unique cells for nominal and numeric
    for j in range(0,totalCols):
        for i in range(1,totalRows):
            columnsTemp.append(allData[i][j])
        for item in columnsTemp:
            if not (item in uniqueTemp):
                uniqueTemp.append(item)
        uniqueOfColumn.append("{" + ','.join(uniqueTemp) + "}") 
        uniqueTemp = []
        columnsTemp = []

    # Assigns numeric or nominal to each cell
    for j in range(1,totalRows):
        for i in range(0,totalCols):
            try:
                if allData[j][i] == str(float(allData[j][i])) or allData[j][i] == str(int(allData[j][i])):
                    dataType.append("numeric")
            except ValueError as e:
                    dataType.append("nominal")

    for j in range(0,totalCols): 
        p = j
        for i in range(0,(totalRows-1)): 
            dataTypeTemp.append(dataType[p])
            p += totalCols  
        if "nominal" in dataTypeTemp:
            finalDataType .append("nominal")
        else:
            finalDataType .append("numeric")
        dataTypeTemp = []

    for i in range(0,len(finalDataType )):
        if finalDataType [i] == "nominal":
            attTypes.append(uniqueOfColumn[i])
        else:
            attTypes.append(finalDataType[i])

    # Show comments
    writeFile.write("%\n% Comments go after a '%' sign.\n%\n")
    writeFile.write("%\n% Relation: " + relation +"\n%\n%\n")
    writeFile.write("% Attributes: " + str(totalCols) + " "*5 
        + "Instances: " + str(totalRows-1) + "\n%\n%\n\n")

    # Show Relation
    writeFile.write("@relation " + relation + "\n\n")

    # Show Attributes
    for i in range(0,totalCols):
        writeFile.write("@attribute" + " '" + attributes[i] 
            + "' " + attTypes[i] + "\n")

    # Show Data
    writeFile.write("\n@data\n")
    for i in range(1,totalRows):
        writeFile.write(','.join(allData[i])+"\n")

    print(fileToRead + " was converted to " + fileToWrite)


def start(message, fs_csvs, fs_arffs, channel):
    message = json.loads(message)

    # create empty temp file
    tf = tempfile.NamedTemporaryFile()
    # csv contents
    out = fs_csvs.get(ObjectId(message["csv_fid"]))
    # add csv contents to empty file 
    tf.write(out.read())

    # write arff to the file
    tf_path = tempfile.gettempdir() + f"/{message['csv_fid']}.arff"
   
    # create arff from temp csv file
    csv_2_arff(tf.name, tf_path, "dataset"),
    
    tf.close()

    # save file arff to mongo
    f = open(tf_path, "rb")
    data = f.read()
    fid = fs_arffs.put(data)
    f.close()
    os.remove(tf_path)

    message["arff_fid"] = str(fid)

    try:
        channel.basic_publish(
            # publish a message on the mp3 queue to signal that there is a file available
            exchange="",
            routing_key=os.environ.get("ARFF_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        # error in publish the message on the queue -> delete the mo3 file from the mongo db
        fs_arffs.delete(fid)
        return "failed to publish message"