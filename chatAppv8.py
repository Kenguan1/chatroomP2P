from tkinter import *
from tkinter.ttk import *
import socket
import _thread
import time
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode
from base64 import b64decode
from tkinter import filedialog
import sv_ttk


class ChatClient(Frame):
  
  def __init__(self, root):
    Frame.__init__(self, root)
    self.root = root
    self.initUI()
    self.serverSoc = None
    self.serverStatus = 0
    self.buffsize = 1024
    self.allClients = {} #Diccionario de objetos socket
    self.counter = 0

  
  def initUI(self):
    #Definición interfaz gráfica
    self.root.title("Chatroom P2P")
    self.FrameSizeX  = 705
    self.FrameSizeY  = 530
    ScreenSizeX = self.root.winfo_screenwidth()
    ScreenSizeY = self.root.winfo_screenheight()
    FramePosX   = int((ScreenSizeX - self.FrameSizeX)/2)
    FramePosY   = int((ScreenSizeY - self.FrameSizeY)/2)
    self.root.geometry("%sx%s+%s+%s" % (self.FrameSizeX,self.FrameSizeY,FramePosX,FramePosY))

    #fondo ventana
    self.root.configure(bg='skyblue4')

    style = Style()
  
    

    #Letra botones
    style.configure('TButton', font =
               ('arial', 11, 'bold'),
                foreground = 'skyblue4')

    #hover
    style.map('TButton', foreground = [('active', '!disabled', 'green')],
                     background = [('active', 'black')])

  
    padX = 10
    padY = 10
    parentFrame = Frame(self.root)
    parentFrame.grid(padx=padX, pady=padY, stick=E+W+N+S
    )
    
    ipGroup = Frame(parentFrame)

    serverLabel = Label(ipGroup, text="Apodo:", font=("Helvetica", 12))
    self.nameVar = StringVar()
    self.nameVar.set("")
    nameField = Entry(ipGroup, width=10, textvariable=self.nameVar)
    self.serverIPVar = StringVar()
    self.serverIPVar.set("127.0.0.1")
    serverIPField = Entry(ipGroup, width=15, textvariable=self.serverIPVar)
    self.serverPortVar = StringVar()
    self.serverPortVar.set("30001")
    serverPortField = Entry(ipGroup, width=5, textvariable=self.serverPortVar)
    serverSetButton = Button(ipGroup, text="Listo", width=10, command=self.handleSetServer)

    addClientLabel = Label(ipGroup, text="Unirse a: ", font=("Helvetica", 12))
    self.clientIPVar = StringVar()
    self.clientIPVar.set("127.0.0.1")
    clientIPField = Entry(ipGroup, width=15, textvariable=self.clientIPVar)
    self.clientPortVar = StringVar()
    self.clientPortVar.set("30002")
    clientPortField = Entry(ipGroup, width=5, textvariable=self.clientPortVar)
    clientSetButton = Button(ipGroup, text="Unirse", width=10, command=self.handleAddClient)
    
    serverLabel.grid(row=0, column=0) #"Apodo:"
    nameField.grid(row=0, column=1)   #gap del nombre
    serverIPField.grid(row=0, column=2) #gap de ip
    serverPortField.grid(row=0, column=3) #gap del puerto
    serverSetButton.grid(row=0, column=4, padx=5, pady=5)
    addClientLabel.grid(row=0, column=5)
    clientIPField.grid(row=0, column=6)
    clientPortField.grid(row=0, column=7)
    clientSetButton.grid(row=0, column=8, padx=5, pady=5)
    
    readChatGroup = Frame(parentFrame)
    self.receivedChats = Text(readChatGroup, bg="white", width=60, height=21, state=DISABLED, background='slategray1', font=('Arial 11')) #Chats del chatroom
    self.friends = Listbox(readChatGroup, bg="white", width=30, height=21, background='slategray2', foreground="black") #lista de amigos
    self.receivedChats.grid(row=0, column=0, sticky=W+N+S, padx = (0,10))
    self.friends.grid(row=0, column=1, sticky=E+N+S)
    self.receivedChats.tag_config('private', foreground="blue") #COLOR MENSAJE PRIVADO

    writeChatGroup = Frame(parentFrame)
    self.chatVar = StringVar()
    self.chatField = Entry(writeChatGroup, width=77, textvariable=self.chatVar) #input de dónde se escribe

    sendChatButton = Button(writeChatGroup, text="Enviar", width=10, command=self.handleSendChat) #Boton Envio
    sendChatButtonP = Button(writeChatGroup, text="Enviar Priv", width=10, command=self.privado) #Boton privado
    sendImageButton = Button(writeChatGroup, text="Imagen", width=10, command=self.handleSendImage) #Boton imagen

    self.chatField.grid(row=0, column=0, sticky=W)
    sendChatButton.grid(row=0, column=1, padx=10)
    sendChatButtonP.grid(row=1, column=1, padx=10, pady=8)
    sendImageButton.grid(row=0, column=2, padx=0)

    self.statusLabel = Label(parentFrame)

    bottomLabel = Label(parentFrame, text="Juan Camilo García Braham - Camilo Kenguan Sanchez. Basado en: https://github.com/sdht0/P2P-chat-application")
    
    ipGroup.grid(row=0, column=0)
    readChatGroup.grid(row=1, column=0)
    writeChatGroup.grid(row=2, column=0, pady=10)
    self.statusLabel.grid(row=3, column=0)
    bottomLabel.grid(row=3, column=0, pady=0)
    
#Funciones del chatroom
  #Creación del chatroom
  def handleSetServer(self):
    print("Creación de chatroom")
    if self.serverSoc != None:
        self.serverSoc.close()
        self.serverSoc = None
        self.serverStatus = 0
    serveraddr = (self.serverIPVar.get().replace(' ',''), int(self.serverPortVar.get().replace(' ',''))) #la ip y puerto que ingresamos de forma manual
    try:
        self.serverSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSoc.bind(serveraddr)
        self.serverSoc.listen(5)
        self.setStatus("Server listening on %s:%s" % serveraddr)
        _thread.start_new_thread(self.listenClients,())
        self.serverStatus = 1
        self.name = self.nameVar.get().replace(' ','')
        if self.name == '':
            self.name = "%s:%s" % serveraddr
    except:
        self.setStatus("Error al configurar el servidor.")
    
  def listenClients(self):
    print("Acepta clientes")
    while 1:
      clientsoc, clientaddr = self.serverSoc.accept()
      #Mandar nombre de usuario
      clientsoc.send((self.name).encode())
      self.setStatus("Cliente conectado desde %s:%s" % clientaddr)
      nombre_cliente=clientsoc.recv((self.buffsize)).decode()
      print("hola "+nombre_cliente)
      self.addClient(nombre_cliente, clientsoc, clientaddr)
      _thread.start_new_thread(self.handleClientMessages, (clientsoc, clientaddr, nombre_cliente)) #inicializamos un hilo
    self.serverSoc.close()
  
  def handleAddClient(self):
    print("Añade clientes")
    if self.serverStatus == 0:
      self.setStatus("Primero coloque la dirección del chatroom")
      return
    clientaddr = (self.clientIPVar.get().replace(' ',''), int(self.clientPortVar.get().replace(' ','')))
    for port in range(30001,30005): #5 PERSONAS max PARA CHAT GRUPAL, si queremos aumentar aumentamos el rango
      try:
        if port == int(self.serverPortVar.get().replace(' ','')): #si el puerto ya está entonces que no se repita en la lista
          pass
        else:
          clientsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          print(port)
          address=("127.0.0.1", port)
          clientsoc.connect(address)
          self.setStatus("Conectado a cliente en %s:%s" % address)
          nombre_cliente=(clientsoc.recv(self.buffsize)).decode()
          clientsoc.send((self.name).encode())
          self.addClient(nombre_cliente, clientsoc, address)
          _thread.start_new_thread(self.handleClientMessages, (clientsoc, address, nombre_cliente))
      except:
        self.setStatus("Error al conectarse con el cliente.")

  def handleClientMessages(self, clientsoc, clientaddr, nombre_cliente):
    while 1:
      try:
        """ ENCRIPTACIONNN """
        data1 = clientsoc.recv(self.buffsize)
        codigo=data1[0] #primer byte es para saber si el mensaje es publico, privado o una imagen
        print("CÓDIGO " +str(codigo))
        if codigo==50: #Los códigos llegan de forma distinta a como se envian. b'0'=48=Chat público, b'1'=49=Chat privado, b'2'=50=Imagen
          imagen=open("imagen_recibida.jpg", "wb")
          image_chunk=clientsoc.recv(2048)
          while image_chunk:
            imagen.write(image_chunk)
            image_chunk= clientsoc.recv(2048)
          imagen.close()
        else:  #si no se trata de una imagen recibimos el resto de elementos necesarios para decodificar y desencryptar el mensaje
          llave=data1[1:17] #la llave ocupa 16 bytes por eso se agarra de la 1 a la 17
          print("Llave: "+str(llave))
          iv = data1[17:41] #Variable requerida para encriptación AES modo CFB
          print("IV: "+str(iv))
          iv = b64decode(iv)
          data = data1[41:] #el mensaje ocupa del byte 41 para adelante
          print("MENSAJE CIFRADO: "+str(data))
          ct = b64decode(data)
          cifrado = AES.new(llave, AES.MODE_CFB, iv=iv)
          decipher_text = cifrado.decrypt(ct) #una vez desencryptamos decipher_text es lo que le mandaremos a addChat o addChatPrivate para que se muestre en pantalla
          if not data:
              break
          if codigo==49: #si es privado
            self.addChatPrivate(nombre_cliente + " (%s:%s)" % clientaddr, decipher_text)
          else: #si es público
            self.addChat(nombre_cliente + " (%s:%s)" % clientaddr, decipher_text)
      except:
          break
    self.removeClient(clientsoc, clientaddr)
    clientsoc.close()
    self.setStatus("Client desconectado desde %s:%s" % clientaddr)

  
  def handleSendChat(self):
    if self.serverStatus == 0:
      self.setStatus("Primero coloque la dirección del chatroom")
      return
    """----ENCRIPTACIONNN----"""
    msg = self.chatVar.get().replace(' ',' ').encode() #tomamos lo que se escribió en el "input" chatVar y lo codificamos
    print(str(msg))
    llave = get_random_bytes(16) #creamos una llave aleatoria de 16 bytes
    print("Llave: "+str(llave))
    cifrado = AES.new(llave, AES.MODE_CFB) #hacemos el cifrado AES con la llave previamente creada
    msg_cifrado_b = cifrado.encrypt(msg) #ya con el cifrado AES encryptamos el mensaje
    iv = b64encode(cifrado.iv)
    print("IV: "+str(iv))
    ct = b64encode(msg_cifrado_b) #el mensaje ya encryptado lo codificamos base 64 ya para poderlo mandar
    print("TEXTO CIFRADO: " +str(ct))
    if msg == '':
        return
    self.addChat("Yo", msg) #se muestra el mensaje sin encryptar en pantalla
    """ ENCRIPTACIONNN """
    privado=b'0'
    for client in self.allClients.keys():
      client.send(privado+llave+iv+ct)  #se manda un mensaje que tiene 4 componentes en una linea a la función HandleClientMessage que descompone este mensaje

      #privado será un binario, que servirá para identificar el tipo de mensaje, en este caso definimos como 0 ya que es mensaje a chat grupal
      #llave ocupara 16 bytes y es la forma de encryptación
      #iv hace parte del protocolo AES
      #ct es el mensaje cifrado con la respectiva llave y protocolo 
  

  def handleSendChatPrivate(self, peer): #para enviar mensaje privado hacemos lo mismo que HandleSendChat pero mandando el peer que queramos buscar
    if self.serverStatus == 0:
      self.setStatus("Primero coloque la dirección del chatroom")
      return
    """----ENCRIPTACIONNN----"""
    msg = self.chatVar.get().replace(' ',' ').encode()
    print(str(msg))
    llave = get_random_bytes(16)
    print("Llave: "+str(llave))
    cifrado = AES.new(llave, AES.MODE_CFB)
    msg_cifrado_b = cifrado.encrypt(msg)
    iv = b64encode(cifrado.iv)
    print("IV: "+str(iv))
    ct = b64encode(msg_cifrado_b)
    print("TEXTO CIFRADO: " +str(ct))
    if msg == '':
        return
    self.addChat("Yo", msg)
    """ ENCRIPTACIONNN """
    privado=b'1' #aqui definimos a privado=1 ya que estamos mandando un mensaje privado
    for client in self.allClients.keys(): #se hace un ciclo buscando el peer que le mandamos a esta función, vamos comparando usando el método getpeername()
      if client.getpeername()==peer:
        client.send(privado+llave+iv+ct) #una vez encontramos el peer le mandamos el mensaje 


  def handleSendImage(self):
    if self.serverStatus == 0:
      self.setStatus("Primero coloque la dirección del chatroom")
      return
      #Cargar imagen
    direcccion=filedialog.askopenfilename(title="Seleccione la imagen",
                                           filetypes=(("JPG", "*.jpeg"),
                                          ))
    imagen=open(direcccion, "rb")
    data_imagen=imagen.read(2048)

    self.addChatImage("Yo", "IMAGEN ENVIADA"+"\n")
    for client in self.allClients.keys():
        client.send(b"2")  #ENVIO DE IMAGENES A CADA NODO
        while data_imagen:
          client.send(data_imagen)
          data_imagen=imagen.read(2048)
        imagen.close()


  def privado(self,*args):
    chat = self.friends.curselection() #el chat que seleccionemos con el cursor
    peer = self.friends.get(chat)
    peer = peer.split(" ")
    peer = peer[1]
    peer = peer[1:len(peer)-1]
    peer = peer.split(":")
    peer[1] = int(peer[1])
    peer = tuple(peer) #peer lo convertimos en una tupla para que se pueda reconocer cuándo lo comparamos en la funcion handleSendChatPrivate
    self.handleSendChatPrivate(peer)


  def addChatImage(self, nombre_cliente, msg ):
    self.receivedChats.config(state=NORMAL)
    self.receivedChats.insert("end",nombre_cliente+": "+msg)
    print(type(nombre_cliente))
    self.receivedChats.config(state=DISABLED)


  def addChat(self, nombre_cliente, msg ): #SE MUESTRA ASÍ EN PANTALLA
    self.receivedChats.config(state=NORMAL)
    self.receivedChats.insert("end",nombre_cliente+": "+msg.decode()+"\n")
    self.receivedChats.config(state=DISABLED)
  
  def addChatPrivate(self, nombre_cliente, msg ):
    self.receivedChats.config(state=NORMAL)
    self.receivedChats.insert("end","[PRIVADO] "+nombre_cliente+": "+msg.decode()+"\n", "private") #se manda el atributo "private" a receivedChats para poner el color azul (line99)
    self.receivedChats.config(state=DISABLED)
  
  def addClient(self, nombre_cliente, clientsoc, clientaddr):
    self.allClients[clientsoc]=self.counter
    self.counter += 1
    self.friends.insert(self.counter,nombre_cliente+" (%s:%s)" % clientaddr)

  
  def removeClient(self, clientsoc, clientaddr):
      self.friends.delete(self.allClients[clientsoc])
      del self.allClients[clientsoc]
      print(self.allClients)
  
  def setStatus(self, msg):
    self.statusLabel.config(text=msg)
    print(msg)
      
def main():  
  root = Tk()
  app = ChatClient(root)
  root.mainloop()  

if __name__ == '__main__':
  main()  