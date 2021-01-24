import socket
import os
import time
import threading
import multiprocessing



def startSending(clientSock):
    reqMsg = clientSock.recv(1024)  # get the request msg
    #Uncomment line below if you want to test for 408
    #time.sleep(15)
    splitMessage = reqMsg.split(b'\r\n') #Split by carriage returns so we can get the individual request headers
    splitPath = splitMessage[0].split(b' ') #Split the first header, so we can get the requested path
    filePath = splitPath[1][1:] #get rid of the /
    
    #Get the If-Last-Modified Date
    lastModified = splitMessage[9]
    lastModified = lastModified[19:].decode("utf-8")

    f = None
    # Try to open the file, if not found, send error code 404
    try:
        f = open(filePath, 'r')  
    except OSError:
        clientSock.sendall(str.encode("""HTTP/1.1 404 NOT FOUND\n""",'iso-8859-1'))
        clientSock.sendall(str.encode('Content-Type: text/html\n', 'iso-8859-1'))
        clientSock.send(str.encode('\n'))
        clientSock.sendall(str.encode("""
            <html>
            <body>
            <h1>ERROR CODE 404: File Not Found
            </body>
            </html>
        """)) 

    if f != None: #If file exists
        #Check if the file has ever been accesed len(lastModified == 0) or it has been modified (lastModified != time)
        fileLastModified = time.ctime(os.stat(filePath)[8])
        if ((len(lastModified) == 0) or (lastModified != fileLastModified)):
            l = f.read(1024)
            while (l):
                #Set HTTP headers, status, content type and last modified
                clientSock.sendall(str.encode("""HTTP/1.1 200 OK\n""",'iso-8859-1'))
                clientSock.sendall(str.encode('Content-Type: text/html\n', 'iso-8859-1'))
                concat = 'Last-Modified: ' + fileLastModified
                clientSock.sendall(str.encode(concat, 'iso-8859-1'))
                clientSock.send(str.encode('\n'))
                
                #Send the requested file
                clientSock.sendall(str.encode(""+l+"", 'iso-8859-1'))
                l = f.read(1024)
            f.close()
            #If file has not been modified throw a 304 and 400 error code
            #Mozilla has repeated a request without modification has an example of a 400 error code
            #https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400 

        else:#Display 400 error
            clientSock.sendall(str.encode("""HTTP/1.1 400 BAD REQUEST\n""",'iso-8859-1'))
            clientSock.sendall(str.encode('Content-Type: text/html\n', 'iso-8859-1'))
            concat = 'Last-Modified: ' + fileLastModified
            clientSock.sendall(str.encode(concat, 'iso-8859-1'))

            clientSock.send(str.encode('\n'))
            clientSock.sendall(str.encode("""
                <html>
                <body>
                <h1>ERROR CODE 400: Bad Request The client should not repeat this request without modification (HTTP 304: Not Modified)
                </body>
                </html>
            """)) 
    clientSock.close()

def main():
    # Create TCP Socket, Bind, then start to listen for requests
    port = 8001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostbyname(socket.gethostname())
    print("Binding to Host:",host, "on Port:",port)
    sock.bind((host, port))
    sock.listen(5) 
    while True:
        print("LISTENING")
        clientSock, clientAddr = sock.accept()
        #Start the startSending function, using p to manage request time out
        p = multiprocessing.Process(target=startSending, name="startSending", args=(clientSock,))
        p.start()
 
        #If startSending finishes before 5 seconds, join and bypass p.is_alive()
        #you can change this value to any arbitrary number
        p.join(5)
        
        #If startSending is still running after the 5 seconds, display HTTP Error 408
        if p.is_alive():
            # Terminate startSending
            p.terminate()
            p.join()
            
            #Display 408
            clientSock.sendall(str.encode("""HTTP/1.1 408 REQUEST TIMED OUT\n""",'iso-8859-1'))
            clientSock.sendall(str.encode('Content-Type: text/html\n', 'iso-8859-1'))
            clientSock.send(str.encode('\n'))
            clientSock.sendall(str.encode("""
                <html>
                <body>
                <h1>ERROR CODE 408: REQEUEST TIMED OUT
                </body>
                </html>
            """)) 
        clientSock.close()


if __name__ == '__main__':
    main()