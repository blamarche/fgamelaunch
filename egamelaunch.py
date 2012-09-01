#!/usr/bin/python
#fgamelaunch:Console game launcher based on the concept of dgamelaunch
#
############License Info#####################
#fgamelaunch (C) 2010 dracflamloc (dracsoft.com)
#
#This program is free software; you can redistribute it and/or modify 
#it under the terms of the GNU General Public License as published by 
#the Free Software Foundation; either version 2 of the License, or 
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful, 
#but WITHOUT ANY WARRANTY; without even the implied warranty of 
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#GNU General Public License for more details. 
#
#You should have received a copy of the GNU General Public License 
#along with this program; if not, write to the Free Software 
#Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#############################################
#
#
#
#egamelaunch:Console game launcher based on the concept of dgamelaunch
#
############License Info#####################
#egamelaunch (C) 2008 Emmanuel Jacyna
#
#This program is free software; you can redistribute it and/or modify 
#it under the terms of the GNU General Public License as published by 
#the Free Software Foundation; either version 2 of the License, or 
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful, 
#but WITHOUT ANY WARRANTY; without even the implied warranty of 
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#GNU General Public License for more details. 
#
#You should have received a copy of the GNU General Public License 
#along with this program; if not, write to the Free Software 
#Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#############################################
#
#

__author__='dracflamloc, Emmanuel Jacyna'
__email__='drac@dracsoft.com'
__license__='GPL v2'
__status__='Alpha'

import os,pickle
import curses
import time

current_tty_recordfile=""

### Useful little functions...
def sortfiles_desc(a,b):
    if a<b:
        return 1
    if a>b:    
        return -1
    if a==b:
        return 0
    
def bool(x):
    '''Return a boolean value (True or False) depending on the contents of x.
slightly different from python's builtin bool function, because it evaluates
strings of "True","False","T","F", etc..
Only works on strings.'''
    if x.lower() == "true" or x.lower() == "t":
        return True
    elif x.lower() == "false" or x.lower() == "f":
        return False
    elif x:return True
    else:return False
    
def chr_safe(x):
    '''Convert a number sequence to a character.
Returns the number sequence of the character if it is above 256.'''
    if x > 256:return x
    else:return chr(x)
    
def has_chars(x,chars):
    '''Return True if any of the characrers in chars is in x.'''
    i=0
    for char in chars:
        if char in x:return True
        i+=1       
    return False
    
def error(win,type,str):
    if type == 'name':
        #Catch duplicate names
        if str in [v.name for v in win.PLAYERS.values()]:return True
        #If whitespace or a blank line is entered, exit dialog
        elif has_chars(str,"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""):return True
    elif type == 'email':
        if len(str.split('@')) != 2:return True
        elif '.' not in str.split('@')[1]:return True
        elif not str.split('@')[1].strip('.'):return True
    return False
        
    
## Exceptions
class EGLError(Exception):pass
class ConfigError(EGLError):pass

## Classes
class Player:
    def __init__(self,name,password,email):
        '''Player is a simple class to hold player variables'''
        self.name=name
        self.password=password
        self.email=email

class Game:
    '''Simple class to hold game variables...'''
    def __init__(self,name,short_name,handler,path,rcfile,num,args,extras=None):
        self.name=name
        self.short_name=short_name
        self.path=path
        if rcfile == 'None':self.rcfile=None
        else:self.rcfile=rcfile
        self.num=num
        if not args:
            self.args=""
        else:self.args=args
        self.handler=handler
        self.extras=extras
    def __str__(self):
        return """%(name)s - %(short_name)s\nHandler:%(handler)s\nPath:%(path)s
Arguments:%(args)s\nGame Number:%(num)s\nExtra Info:%(extras)s"""%self.__dict__
        

class window:
    '''Our main ncurses window'''

    def parse_config(self,cfg):
        '''Parse the config file.
Add variables to self.OPTIONS and Game objects to self.games'''    
        cfg=open(cfg)
        #The options that are considered legal
        legal_opts=['GAME','GAMESTART','GAMEEND','name','short_name','args',\
        'path','rcfile','num','handler','TTYREC','TTYRECBIN','BANNER','TTYRECDIR','USERDIR','SERVER_NAME',\
        'MAXUSERS','MAX_USERNAME_LEN','ADMIN_EMAIL']
        #Are we in a game definition?
        gamedef=0
        line_no=1
        #Temporary holder for game definition variables,before we 
        #construct a game object
        cur_game={'extras':{}}
        try:
            for line in cfg.readlines():
                error=''
                opt=line.strip().split('=')
                if not line.strip():pass           
                elif '#' in opt[0]:pass
                #We want to be able to accept arbitrary options
                #in a gamedef for extras
                elif opt[0] not in legal_opts and not gamedef:
                    error='Invalid option'
                    raise ConfigError          
                #Game stuff
                elif opt[0] == 'GAMESTART':gamedef=1
                elif opt[0] == 'GAMEEND':
                    #Try to instantiate the game.
                    try:
                        self.games[cur_game['num']]=Game(cur_game['name'],\
                        cur_game['short_name'],cur_game['handler'],\
                        cur_game['path'],cur_game['rcfile'],cur_game['num'],\
                        cur_game['args'],cur_game['extras'])
                    except KeyError:
                        error='Option missing in game definition'
                        raise ConfigError                      
                    gamedef=0
                    cur_game={'extras':{}}
                elif gamedef:
                    if opt[0]=='name':cur_game['name']=opt[1]                 
                    elif opt[0]=='path':cur_game['path']=opt[1]
                    elif opt[0]=='rcfile':
                        if opt[1] == None:cur_game['rcfile']=None
                        else:cur_game['rcfile']=opt[1]
                    elif opt[0]=='args':
                        try:cur_game['args']+=(' '+opt[1])
                        except KeyError:cur_game['args']=opt[1]
                    elif opt[0]=='handler':cur_game['handler']=opt[1]
                    elif opt[0]=='num':cur_game['num']=int(opt[1])
                    elif opt[0]=='short_name':cur_game['short_name']=opt[1]
                    else:cur_game['extras'][opt[0]]=opt[1]
                #Rest of the options
                elif opt[0] == 'TTYREC':self.ttyrec=bool(opt[1])                          
                elif opt[0] == 'BANNER':
                    banner=open(opt[1])#open the banner file
                    self.banner=banner.readlines()
                    if len(self.banner) > 11:
                        error='Banner file too long. (Can only be 11 lines)'
                        raise ConfigError,error
                    banner.close()
                elif opt[1].isdigit():self.OPTIONS[opt[0]]=int(opt[1])
                else:self.OPTIONS[opt[0]]=opt[1]
                line_no+=1
        except:
            raise ConfigError,'problem with configuration file:%s\nLine %s\n%s'\
            %(cfg.name,line_no,error)
        finally:cfg.close()
        
    def __init__(self,cfg):
        #Initialise variables
        self.OPTIONS={}
        self.games={}
        #Dunno whether I'll end up using this...
        self.cur_game=None
        #Used for dispatching in main
        #If it's in the 0 group, it is used for dispatching in the main menu
        #And if it's in the 1 group, for dispatching in the "logged in" menu
        self.commands={\
        0:{'l':'self.login','w':'self.watch_games','r':'self.replay_games','q':'self.quit'},\
        1:{'w':'self.watch_games','r':'self.replay_games','q':'self.quit','p':'self.play'}}
        
	    #self.commands={\
        #0:{'r':'self.register','l':'self.login','q':'self.quit'},\
        #1:{'e':'self.change_email','c':'self.change_pass',\
        #'q':'self.quit','p':'self.play'}}
		
	   #Parse the config file
        self.parse_config(cfg)
        try:
            os.mkdir('%(TTYRECDIR)s'%(self.OPTIONS))
        except:
            was_err_creating_ttyrecfolder=True
        #Edit
        #for k in self.games.keys():
         #   self.commands[1][str(k)]='self.gamec(%s)'%k
        #Load the players into self.PLAYERS
        #try:
        #    fout=open('%(USERDIR)s/players.pkl')%self.OPTIONS
        #    self.PLAYERS=pickle.load(fout)
        #    fout.close()
        #If the file doesn't exist self.PLAYERS is an empty dictionary
        #except:
        self.PLAYERS={}            
        #The screen will be initialised in the function main
        self.screen=None
        #Whether logged in or not...Testing..
        self.cur_user=None#self.PLAYERS['test']
        
    def __call__(self,winobj):
        self.main()
    
### Wrapper functions ###############################
            
    def clear(self):
        '''Clear the screen, keeping the server name at the top'''
        self.screen.clear()
        self.screen.addstr(0,1,'%(SERVER_NAME)s'%self.OPTIONS)
        self.screen.refresh()
        
### Menu functions #################################

    def login(self):
        '''Add a new player to self.PLAYERS and then log into it'''
        self.clear()
        #Do not allow a register if MAXUSERS exceeded
        #if len(self.PLAYERS)+1 > self.OPTIONS['MAXUSERS']:
        #    self.screen.addstr(4,1,'Sorry, too many users are signed in.')
        #    try:self.screen.addstr(5,1,'You might email %(ADMIN_EMAIL)s.'\
        #    %self.OPTIONS)
        #    except KeyError:self.addstr(6,1,'You might email the server admin.')
        #    self.screen.addstr(6,1,'Hit ENTER to go back to the menu.')
        #    return self.screen.getch()
        ## Get the name
        #Turn echoing on to get the name
        curses.echo()
        safe=0
        while not safe:
            self.screen.addstr(4,1,'Welcome user. Please enter a nickname.')
            self.screen.addstr(5,1,'Only characters and numbers are allowed.')
            self.screen.addstr(7,1,'%(MAX_USERNAME_LEN)d character max (blank li\
ne aborts)'%self.OPTIONS)
            self.screen.addstr(9,1,'=>')
            name=self.screen.getstr(self.OPTIONS['MAX_USERNAME_LEN'])
            #Catch duplicate names
            #if error(self,'name',name):
            #    self.screen.addstr(12,1,'Nickname in use!',curses.A_BOLD)
            #    self.screen.move(9,1)
            #    self.screen.clrtoeol()
            if not name.strip():return
            else:safe=1
               
        ##Add the new player
        self.PLAYERS[name]=Player(name,"","")
        #Login
        self.cur_user=self.PLAYERS[name]
        #Dump PLAYERS to file
        fout=open(self.OPTIONS['PLAYERS_DICT'],'w')
        pickle.dump(self.PLAYERS,fout)
        fout.close()
        #Create the user's directory
        os.mkdir('%(USERDIR)s/%s'%(self.OPTIONS,name))        

    def login_old(self):
        '''Get a username and password, and change cur_user to the corresponding
Player object,thereby logging in'''
        self.clear()
        
        curses.echo()
        #Get the username
        safe=0
        while not safe:
            self.screen.addstr(4,1,'Please enter your username. (blank line aborts)')
            self.screen.addstr(6,1,'=>')       
            name=self.screen.getstr()
            if not name.strip():return
            elif name not in [v.name for v in self.PLAYERS.values()]:
                self.screen.addstr(12,0,\
                'There was a problem with your last entry',curses.A_BOLD)
                self.screen.move(6,1)
                self.screen.clrtoeol()
            else:safe=1
        curses.noecho()
        self.clear()
        safe=0
        while not safe:        
            self.screen.addstr(4,1,\
            'Please enter your password. (blank line aborts)')
            self.screen.addstr(6,1,'=>')
        #Get the password
            passwd=self.screen.getstr()
            if passwd == self.PLAYERS[name].password:
                self.cur_user=self.PLAYERS[name]
                safe=1
            elif not passwd.strip():return
            else:
                self.screen.addstr(12,0,\
                'There was a problem with your last entry.',curses.A_BOLD)
                self.screen.move(6,1)
                self.screen.clrtoeol()
        
    def change_email(self):
        '''Change self.cur_user's email address'''
        self.clear()
        safe=0
        curses.echo()
        while not safe:
            self.screen.addstr(4,1,'Your current email is: %s'\
            %self.cur_user.email)
            self.screen.addstr(5,1,\
            'Please enter your new one (80 character max, blank line aborts)')
            self.screen.addstr(7,1,'=>')
            email=self.screen.getstr(80)
            
            if not email.strip():return
            elif email==self.cur_user.email:
                self.screen.addstr(11,1,"That's the same as your old one!",\
                curses.A_BOLD)
                self.screen.move(7,1)
                self.screen.clrtoeol()
            elif error(self,'email',email):
                self.screen.addstr(11,1,"That doesn't look like an email",\
                curses.A_BOLD)
                self.screen.move(7,1)
                self.screen.clrtoeol()
            else:safe=1
        self.cur_user.email=email
    
    def change_pass(self):
        '''Change self.cur_user's password, or return a password for register.'''
        #Turn echoing off for the password.
        curses.noecho()
        safe=0
        self.clear()
        while not safe:
            #So we can use this in register
            if self.cur_user:self.screen.addstr(4,1,\
            'Please enter a new password.')
            else:self.screen.addstr(4,1,'Please enter a password.')
            self.screen.addstr(5,1,\
'Remember, this will be sent over an insecure')
            self.screen.addstr(6,1,'internet connection, so make it something new.')
            self.screen.addstr(7,1,'80 character max. (blank line aborts)')
            self.screen.addstr(9,1,'=>')
            passwd=self.screen.getstr(80)
            #In case the password is nothing, exit dialog
            if not passwd.strip():return
            else:safe=1
        safe=0
        while not safe:
            self.screen.addstr(11,1,'And again.')
            self.screen.addstr(13,1,'=>')
            check=self.screen.getstr(80)
            if not check.strip():return
            elif check != passwd:
                self.screen.addstr(15,1,"The passwords don't match. Try again.",\
                curses.A_BOLD)
            else:safe=1
        if self.cur_user:self.cur_user.password=passwd
        else:return passwd
    
    def replay_games(self):
        '''Present menu of games to watch'''
        self.clear()        
        recpath = self.OPTIONS["TTYRECDIR"]
        dirList=os.listdir(recpath+"/")
        dirList.sort(sortfiles_desc)
        i=0
        self.screen.addstr(1,1,'Choose from the most recent 10 games to replay:')
        self.screen.addstr(2,1,"   Game\t\tUser\t\tLast Active")
        for fname in dirList:
            if i>9:
                break
            stats = os.stat(recpath+"/"+fname)
            lastmod_date = time.localtime(stats[8])
            farray = fname.split("-")
            if len(farray)>=3:
                gamename=farray[1]
                username=farray[2]
            else:
                gamename=fname
                username=""
            self.screen.addstr(i+3,1,str(i)+": "+gamename+"\t\t"+username+"\t\t"+time.strftime("%m/%d/%y %H:%M:%S", lastmod_date))
            i=i+1
        
        self.screen.addstr(i+4,1,'=>')        
        game=chr_safe(self.screen.getch())
        game=int(game)
        recfilename = dirList[game]        
        curses.nocbreak()
        self.clear()
        os.system('ttyplay -s 2 %s/%s'%(recpath, recfilename))                
        #os.system('ttyplay -p %s/%s'%(recpath, recfilename))                
        curses.cbreak()                    
    
    def watch_games(self):
        '''Present menu of games to watch'''
        self.clear()        
        recpath = self.OPTIONS["TTYRECDIR"]
        dirList=os.listdir(recpath+"/")
        dirList.sort(sortfiles_desc)
        i=0
        self.screen.addstr(1,1,'Choose from the most recent 10 games to watch:')
        self.screen.addstr(2,1,"   Game\t\tUser\t\tLast Active")
        for fname in dirList:
            if i>9:
                break
            stats = os.stat(recpath+"/"+fname)
            lastmod_date = time.localtime(stats[8])
            farray = fname.split("-")
            if len(farray)>=3:
                gamename=farray[1]
                username=farray[2]
            else:
                gamename=fname
                username=""
            self.screen.addstr(i+3,1,str(i)+": "+gamename+"\t\t"+username+"\t\t"+time.strftime("%m/%d/%y %H:%M:%S", lastmod_date))
            i=i+1
        
        self.screen.addstr(i+4,1,'=>')        
        game=chr_safe(self.screen.getch())
        game=int(game)
        recfilename = dirList[game]        
        curses.nocbreak()
        self.clear()
        #os.system('ttyplay %s/%s'%(recpath, recfilename))                
        os.system('ttyplay -p %s/%s'%(recpath, recfilename))                
        curses.cbreak()                    
    
    def play(self):
        '''Present a menu of games to play'''
        self.clear()
        self.screen.addstr(3,1,'Select a game to play')
        for i in self.games.values():
            self.screen.addstr(3+i.num,1,'%s) Play %s'%(i.num,i.name))
        self.screen.addstr(7,1,'=>')
        game=chr_safe(self.screen.getch())
        game=self.games[int(game)]
        if hasattr(self,'p_%s'%game.handler):
            getattr(self,'p_%s'%game.handler)()
        else:
            recpath = self.OPTIONS["TTYRECDIR"]
            curses.nocbreak()
            if self.ttyrec:
                #os.system('/usr/bin/ttyrec -e %s %s/%s'%(game.path, recpath, time.strftime("%Y%m%dT%H%M%S", time.gmtime())+"-"+game.name+"-"+self.cur_user.name))                
                #os.system(game.path)
                recfilename = time.strftime("%Y%m%dT%H%M%S", time.gmtime())+"-"+game.name+"-"+self.cur_user.name
                global current_tty_recordfile
                current_tty_recordfile = recpath+"/"+recfilename
                os.system(self.OPTIONS["TTYRECBIN"]+' -e %s %s/%s'%(game.path, recpath, recfilename))
                os.remove(recpath+"/"+recfilename)  
                current_tty_recordfile = ''              
            else:
                os.system(game.path)
            curses.cbreak()
        
    def quit(self):
        '''Quit''' 
        raise SystemExit

    def dispatch(self,key):
        '''Call key'''
        try:
            #If not logged in evaluate the non-logged-in commands
            if not self.cur_user:eval(self.commands[0][key])()
            #Else evaluate the logged-in commands              
            elif self.cur_game==None:eval(self.commands[1][key])()
        except KeyError:pass
            
    ### Game handler functions.###
    
    #def p_nethack(self):
    #    '''Play a game of nethack'''
    #    self.clear
    #    curses.nocbreak()
    #    if self.ttyrec:
    #        os.system('ttyrec nethack-%s -a -e nethack -u %s'%(self.cur_user.name,self.cur_user.name))
    #    else:os.system('nethack -u %s'%self.cur_user.name)
    #    curses.cbreak()
        
    
    ### Main function ###
    def main(self):
        ##Curses init stuff##        
        #Make the screen
        self.screen=curses.initscr()
        #Turn keypad on
        self.screen.keypad(1)
        #Turn echoing off        
        curses.noecho()
        banlen=len(self.banner)
        
        #Main loop
        while 1:    
            #If user logged in
            if  self.cur_user:
                self.clear()
                c=1
                for line in self.banner:
                    self.screen.addstr(c,1,line)
                    c+=1
                self.screen.addstr(banlen+2,1,'Logged in as: %s.'\
                %self.cur_user.name)                
                self.screen.addstr(banlen+4,1,'p) Play games')
                self.screen.addstr(banlen+5,1,'w) Watch games')
                self.screen.addstr(banlen+6,1,'r) Replay games')
                self.screen.addstr(banlen+7,1,'q) Quit')
                self.screen.addstr(banlen+9,1,'=>')
                #Dispatch the key pressed
                self.dispatch(chr_safe(self.screen.getch()))
            #If user is not logged in:
            else:               
                self.clear()
                c=1
                for line in self.banner:
                    self.screen.addstr(c,1,line)
                    c+=1
                self.screen.addstr(banlen+2,1,'Not logged in. You must login to play')
                self.screen.addstr(banlen+4,1,'l) Login to play')
                #self.screen.addstr(banlen+5,1,'r) Register new user')                
                self.screen.addstr(banlen+5,1,'w) Watch games')
                self.screen.addstr(banlen+6,1,'r) Replay games')
                self.screen.addstr(banlen+7,1,'q) Quit')
                self.screen.addstr(banlen+9,1,'=>')
                self.dispatch(chr_safe(self.screen.getch()))
                
        


if __name__=='__main__':
    import sys
    if len(sys.argv)>2 and sys.argv[1]=='-c':
        #shell mode
        os.system(sys.argv[2])
        #print sys.argv[2]
        #junk=raw_input()
    else:
        #c=window(sys.argv[1])
        os.chdir('/var/games/egamelaunch')
        c=window('egamelaunch.cfg')
        curses.wrapper(c)
        global current_tty_recordfile
        if current_tty_recordfile!='':
            try:
                os.remove(current_tty_recordfile)
            except:
                junk=0
