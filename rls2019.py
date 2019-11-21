# NOM : Karouia
# PRENOM : Alaedine


import sys, os, time, random, argparse, signal, socket, select




FILENAME = ''   # le nom du fichier à rechercher
                # contient éventuellement des wildcards
DEBUG = True   # option -debug : pour activer les messages de debug
FIRST = True   # option -first-match : on s'arrête au premier fichier trouve
SERVER = True  # option -server

# GLOBALS

list_fils= []
mon_pid = 0
Trouver = False
connexion = None



def debug(msg) :
    """affiche un message de debug sur la sortie d'erreur"""
    if DEBUG :
        sys.stderr.write("[{}] {}\n".format(os.getpid(), msg))
    

def change_dir(directory) :
    """change le répertoire dans lequel le processus s'exécute"""
    t = random.randint(1, 2)
    debug('entre dans le répertoire {} et dort {} sec'.format(directory, t))
    if DEBUG :
        time.sleep(t)
    os.chdir(directory)


def subdirs() :
    """renvoie la liste des sous-répertoires du répertoire courant"""
    return [x for x  in os.listdir() if os.path.isdir(x)]
    
def sys_exit(code) :
    debug('termine avec le code de sortie {}'.format(code))
    sys.exit(code)


def load_options() :
    """initialise les variables globales par rapport aux options saisies sur la ligne de commande"""
    global FILENAME, DEBUG, FIRST, SERVER
    parser = argparse.ArgumentParser()
    parser.add_argument('-debug', action='store_true', help='active le mode debug')
    parser.add_argument('-server', action='store_true', help='active le mode serveur')
    parser.add_argument('-first_match', action='store_true', help="s'arrête au premier fichier trouvé")
    parser.add_argument('FILENAME', type=str, nargs='?', help='le(s) fichier(s) à chercher')
    args = parser.parse_args()
    FILENAME = args.FILENAME
    SERVER = args.server
    DEBUG = args.debug
    FIRST = args.first_match
    if FILENAME == None and not SERVER :
        parser.error('FILENAME doit être spécifié')
        
    

    
def local_ls() :
    """renvoie la liste des fichiers du répertoire courant qui correspondent à FILENAME"""

    (r1, w1) = os.pipe()

    pid = os.fork()
    # fils
    if (pid == 0):
        
        f = os.open('/dev/null', os.O_WRONLY)

        os.close(r1)
       
        os.dup2(w1, 1)
        os.dup2(f, 2)
        os.close(f)
        os.execv("/bin/sh", ["sh", "-c", "ls {}".format(FILENAME)])
          # a tester
        
    # pere
    else:
        os.close(w1)
        buf = os.read(r1, 10000)
        return [x for x in buf.decode().split('\n')  if x != '']


def explorer(dirname, relative_path) :
    """explorateur"""
    global list_fils,  Trouver ,copielist
    
    valeurarret = 1
    copielist = []
    
    change_dir(dirname)
    if not local_ls() and not subdirs():
        sys_exit(1)
    
    for file in local_ls() :
        Trouver = True
        print(os.path.join(relative_path, file))
        
    if not(FIRST and Trouver == True):
        for subdir in subdirs() :
            # on cree un explorateur fils pour chaque sous fichier
            pid = os.fork()
            if pid == 0:
                list_fils = []
                explorer(subdir, os.path.join(relative_path, subdir))
            else:
               
                list_fils.append(pid)
       

    copielist = list_fils[:] #on fait une copie de la liste des fils
    
    for i in range(len(list_fils)):  
        try:
            pid,statut = os.waitpid(0,0) #attend les fils avec le code de sortie 0
        except:
            debug("pas de fils en attente")
            
    for child in copielist :
        
        try:
            pid,statut = os.waitpid(0,0)
            list_fils.remove(pid)
        except:
            # si le signal = SIGUSR1 
            if os.getpid() == mon_pid and Trouver == True:
                sys_exit(0)
           
        # code de sortie d'un fils != 0
        if os.WIFEXITED(statut):
            valeurarret = os.WEXITSTATUS(statut)        
            if valeurarret == 0:
                 Trouver = True
        
        # si le parametre FIRST est activé et qu'on a un fils qui a trouvé :
        if FIRST and Trouver == True:
            for filspid in list_fils:                
                os.kill(filspid, signal.SIGUSR1)                
                
    
            for filspid in list_fils :
                (pid ,statut ) = os.wait()
                list_fils.remove(pid)

    if Trouver == True:
        if os.getpid() == mon_pid:
            return
        else:
            sys_exit(0)
    if os.getpid() == mon_pid:
        return
    else:
        sys_exit(1)

    

def handler (sig, ignore):
    global mon_pid, Trouver, copielist

    if sig == signal.SIGUSR1:
        
        for pidfils in copielist:                
            os.kill(pidfils, signal.SIGUSR1)            
            pid,statut = os.waitpid(pidfils,0)
        #on sort avec le code 2
        sys_exit(2)

    


def exo4(): #pas fini
    global FILENAME
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 5000))
    server_socket.listen(5)
    
    list_input = [server_socket, sys.stdin]
    
    While True:
        readers, writers, errors = select.select(list_input, [], [])
        for socket in readers:
            if socket == server_socket:
                
                client, adress = server_socket.accept()
                list_input.append(client)
                msg = "Saisir le fichier recherché: "
                client.send(msg.encode())


def main() :
    """fonction principale"""
    global mon_pid
    load_options()
    mon_pid = os.getpid()
    
    signal.signal(signal.SIGUSR1, handler)
    
    explorer('.', '')
    
if __name__ == "__main__" :
    main()
