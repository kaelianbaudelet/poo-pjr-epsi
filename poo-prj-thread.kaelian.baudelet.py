# L'objectif de cet exercice est de créer une version simplifiée de l'application Twitter/Thread.
# Cette application s'utilise dans un premier temps via la ligne de commande.

# En tant qu'utilisateur de l'application, je peux :
# - M'inscrire en fournissant un pseudo et un mot de passe.
# - Me connecter en fournissant un pseudo et un mot de passe.
# - Créer un "Post" contenant du texte.
# - Afficher un "Post" au hasard.
# - Commenter un "Post" avec du texte.

# Sur le plan technique, vous devrez utiliser :
# - Une interface nommée 'IDatabase' ainsi que son implémentation 'InMemoryDatabase' pour stocker les objets en mémoire et effectuer les opérations suivantes sur les entités :
#   - Création
#   - Liste
#   - Récupération
# - Un objet nommé 'App' qui servira de point d'entrée de l'application et permettra :
#   - L'inscription d'un nouvel utilisateur
#   - La connexion d'un utilisateur existant
#   - La récupération d'un "Post" au hasard
#   - Une instance de 'IDatabase' sera passée en paramètre lors de la construction d'un objet 'App'.
# - Il y aura une interface ou une classe abstraite nommée 'DatabaseModel' qui contiendra une référence à un objet 'IDatabase'. Par exemple, les classes suivantes hériteront de 'DatabaseModel':
#   - User
#   - Post
# - Un objet nommé 'AppCmd' disposera d'une méthode 'run' permettant d'utiliser l'application via la ligne de commande (Cmd).

# Bonus:
# - Créer un class Database qui stocke les données dans un fichier/ou une BDD. (Fait)
# - Créer un class AppApi qui permet d'utiliser l'application via une API REST. (Pas fait)

import sqlite3 # Utilisation de SQLite3 pour se connecter a une vrai base de donnée
import random # Utilisation de random.choice() pour selectionenr un post aléatoire

# Interface IDatabase
class IDatabase:
    def create_user(self, username, password):
        pass

    def get_user(self, username):
        pass

    def create_post(self, user, text):
        pass

    def get_posts(self):
        pass

    def get_random_post(self):
        pass

    def add_comment(self, post, user, text):
        pass

# Model

class DatabaseModel:
    def __init__(self, database: IDatabase):
        self._database = database

# Class de la vrai base de donnée

class RealDatabase(IDatabase):
    def __init__(self):
        self.database_connection = sqlite3.connect("database.db")
        self.cursor = self.database_connection.cursor() # Connection à la base de donnée
        # Création des tables dans la base de données :
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES Users(username)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES Posts(id),
            FOREIGN KEY (username) REFERENCES Users(username)
            )
        """)

    def create_user(self, username, password):
        """
        Méthode pour créer un utilisateur
        Paramètres: username, password
        Retourne: un objet User
        """
        self.cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
        self.database_connection.commit()
        return User(self, username, password)

    def get_user(self, username):
        """
        Méthode pour récupérer un utilisateur
        Paramètres: username
        Retourne: un objet User ou None
        """
        self.cursor.execute("SELECT username, password FROM Users WHERE username = ?", (username,))
        col = self.cursor.fetchone()
        if col:
            return User(self, col[0], col[1])
        return None

    def create_post(self, user, text):
        """
        Méthode pour créer un post
        Paramètres: user, text
        Retourne: un objet Post
        """
        self.cursor.execute("INSERT INTO Posts (username, text) VALUES (?, ?)", (user.username, text))
        self.database_connection.commit()
        post_id = self.cursor.lastrowid
        return Post(self, post_id, user, text)

    def get_posts(self):
        """
        Méthode pour récupérer tous les posts
        Retourne: une liste d'objets Post
        """
        self.cursor.execute("SELECT id, username, text FROM Posts")
        rows = self.cursor.fetchall()
        posts = []
        for row in rows:
            user = self.get_user(row[1])
            post = Post(self, row[0], user, row[2])
            post.comments = self.get_comments_for_post(post)
            posts.append(post)
        return posts

    def get_comments_for_post(self, post):
        """
        Méthode pour récupérer les commentaires d'un post
        Paramètres: post
        Retourne: une liste d'objets Comment
        """
        self.cursor.execute("SELECT id, username, text FROM Comments WHERE post_id = ?", (post.id,))
        rows = self.cursor.fetchall()
        comments = []
        for row in rows:
            user = self.get_user(row[1])
            comment = Comment(self, row[0], post, user, row[2])
            comments.append(comment)
        return comments

    def get_random_post(self):
        """
        Méthode pour récupérer un post aléatoire
        Retourne: un objet Post ou None
        """
        posts = self.get_posts()
        if not posts:
            return None
        return random.choice(posts)

    def add_comment(self, post, user, text):
        """
        Méthode pour ajouter un commentaire
        Paramètres: post, user, text
        Retourne: un objet Comment
        """
        self.cursor.execute("INSERT INTO Comments (post_id, username, text) VALUES (?, ?, ?)", (post.id, user.username, text))
        self.database_connection.commit()
        comment_id = self.cursor.lastrowid
        return Comment(self, comment_id, post, user, text)
    
# Class de la fausse base de donnée

class InMemoryDatabase(IDatabase):
    def __init__(self):
        self.users = {}
        self.posts = []

    def create_user(self, username, password):
        """
        Méthode pour créer un utilisateur
        Paramètres: username, password
        Retourne: un objet User
        """
        if username in self.users:
            print("\033[0;31m⚠ L'utilisateur existe déjà\033[0m")
        user = User(self, username, password)
        self.users[username] = user
        return user

    def get_user(self, username):
        """
        Méthode pour récupérer un utilisateur
        Paramètres: username
        Retourne: un objet User ou None
        """
        return self.users.get(username)

    def create_post(self, user, text):
        """
        Méthode pour créer un post
        Paramètres: user, text
        Retourne: un objet Post
        """
        post_id = len(self.posts) + 1
        post = Post(self, post_id, user, text)
        self.posts.append(post)
        return post
    
    def get_posts(self):
        """
        Méthode pour récupérer tous les posts
        Retourne: une liste d'objets Post
        """
        return self.posts

    def get_random_post(self):
        """
        Méthode pour récupérer un post aléatoire
        Retourne: un objet Post ou None
        """

        if not self.posts:
            return None
        return random.choice(self.posts)

    def add_comment(self, post, user, text):
        """
        Méthode pour ajouter un commentaire
        Paramètres: post, user, text
        Retourne: un objet Comment
        """
        return post.add_comment(user, text)

# Class des Posts

class Post(DatabaseModel):
    def __init__(self, database, post_id, user, text):
        super().__init__(database)
        self.id = post_id
        self.user = user
        self.text = text
        self.comments = []

    def __str__(self):
        return f"{self.user} : {self.text}"

    def add_comment(self, user, text):
        """
        Méthode pour ajouter un commentaire
        Paramètres: user, text
        Retourne: un objet Comment
        """
        comment = Comment(self._database, None, self, user, text)
        self.comments.append(comment)
        return comment

# Class des Commentaires

class Comment(DatabaseModel):
    def __init__(self, database, comment_id, post, user, text):
        super().__init__(database)
        self.id = comment_id
        self.post = post
        self.user = user
        self.text = text

    def __str__(self):
        return f"{self.user}: {self.text}"
    
# Class des Utilisateurs

class User(DatabaseModel):
    def __init__(self, database, username, password):
        super().__init__(database)
        self.username = username
        self.password = password

    def __str__(self):
        return f"{self.username}"

    def create_post(self, text):
        """
        Méthode pour créer un post
        Paramètres: text
        Retourne: un objet Post
        """
        return self._database.create_post(self, text)

# Class principal de l'app

class App:
    
    def __init__(self, database: IDatabase):
        self._database = database
        self.current_user = None

    def disconnect(self):
        """
        Méthode pour déconnecter l'utilisateur
        """
        if self.current_user:
            print(f"\033[0;32mL'utilisateur \033[1;33m{self.current_user}\033[0;32m à été déconnecté\033[0m")
            self.current_user = None
            input()
        else:
            print("\033[0;31m⚠ Vous n'etes pas connecté\033[0m")
            input()

    def signup(self):
        """
        Méthode pour inscrire un utilisateur
        """
        try:
            username = input('Entréer un nom d\'utilisateur: ')
            password = input('Entréer un mot de passe: ')
            self._database.create_user(username, password)
            print(f"\033[0;32mL'utilisateur {username} à été créer avec succès\033[0m")
        except:
             print("\033[0;31m⚠ L'utilisateur existe déjà.\033[0m")
        input()

    def login(self):
        """
        Méthode pour connecter un utilisateur
        """
        username = input("Entrer votre nom d'utilisateur: ")
        password = input("Entrer votre mot de passe: ")
        user = self._database.get_user(password)
        if user and user.password == password:
            self.current_user = user
            print(f"\033[0;32mL'utilisateur {username} est connecté\033[0m")
        else:
             print("\033[0;31m⚠ Mauvais nom d'utilisateur ou mot de passe.\033[0m")
        input()

    def create_post(self):
        """
        Méthode pour créer un post
        """
        if self.current_user:

            self.current_user.create_post(input("Entrer le texte du post: "))
            print("\033[1;32mPost créer avec succès\033[0m")
        else:
            print("\033[0;31m⚠ Vous devez d'abord vous connecter\033[0m")
        input()

    def display_random_post(self):
        """
        Méthode pour afficher un post aléatoire
        """
        post = self._database.get_random_post()
        if post:
            print("\nVoici un post aléatoire:\n")
            ligne_post = post.text.split('\n')
            taille_max_boite_dialogue = max(len(line) for line in ligne_post)
            taille_boite_dialogue = max(taille_max_boite_dialogue, len(post.user.username)) + 4
            print("\033[1;33m█" + "▀" * (taille_boite_dialogue - 2) + 4*"▀"+ "█\033[0m")
            print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
            print(f"\033[1;33m█   {post.user.username}" + " " * (taille_boite_dialogue - len(post.user.username) - 4) + 3*" "+ "█\033[0m")
            print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
            for ligne in ligne_post:
                print(f"\033[1;33m█   {ligne}" + " " * (taille_boite_dialogue - len(ligne) - 4) + 3*" "+ "█\033[0m")
            print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
            print("\033[1;33m█" + "▄" * (taille_boite_dialogue - 2) + 4*"▄"+ "█\033[0m")
            
            for comment in post.comments:
                print('\n')
                ligne_comment = comment.text.split('\n')
                taille_max_boite_commentaire = max(len(line) for line in ligne_comment)
                taille_boite_commentaire = max(taille_max_boite_commentaire, len(comment.user.username)) + 4
                print("｜   " + "█" + "▀" * (taille_boite_commentaire - 2) + 4*"▀"+ "█\033[0m")
                print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                print(f"｜   █   {comment.user.username}" + " " * (taille_boite_commentaire - len(comment.user.username) - 4) + 3*" "+ "█\033[0m")
                print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                for ligne in ligne_comment:
                    print(f"｜   █   {ligne}" + " " * (taille_boite_commentaire - len(ligne) - 4) + 3*" "+ "█\033[0m")
                print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                print("｜   " + "█" + "▄" * (taille_boite_commentaire - 2) + 4*"▄"+ "█\033[0m")
        else:
            print("\033[0;31m⚠ Il y a aucun posts pour le moment\033[0m")
        input()

    def display_posts(self):
        """
        Méthode pour afficher tous les posts
        """
        posts = self._database.get_posts()

        if len(posts) > 0:
            print("\nVoici le feed:")
            for post in posts:
                print('\n')
                ligne_post = post.text.split('\n')
                taille_max_boite_dialogue = max(len(line) for line in ligne_post)
                taille_boite_dialogue = max(taille_max_boite_dialogue, len(post.user.username)) + 4
                print("\033[1;33m█" + "▀" * (taille_boite_dialogue - 2) + 4*"▀"+ "█\033[0m")
                print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
                print(f"\033[1;33m█   {post.user.username}" + " " * (taille_boite_dialogue - len(post.user.username) - 4) + 3*" "+ "█\033[0m")
                print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
                for ligne in ligne_post:
                    print(f"\033[1;33m█   {ligne}" + " " * (taille_boite_dialogue - len(ligne) - 4) + 3*" "+ "█\033[0m")
                print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
                print("\033[1;33m█" + "▄" * (taille_boite_dialogue - 2) + 4*"▄"+ "█\033[0m")
                
                for comment in post.comments:
                    print('\n')
                    ligne_comment = comment.text.split('\n')
                    taille_max_boite_commentaire = max(len(line) for line in ligne_comment)
                    taille_boite_commentaire = max(taille_max_boite_commentaire, len(comment.user.username)) + 4
                    print("｜   " + "█" + "▀" * (taille_boite_commentaire - 2) + 4*"▀"+ "█\033[0m")
                    print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                    print(f"｜   █   {comment.user.username}" + " " * (taille_boite_commentaire - len(comment.user.username) - 4) + 3*" "+ "█\033[0m")
                    print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                    for ligne in ligne_comment:
                        print(f"｜   █   {ligne}" + " " * (taille_boite_commentaire - len(ligne) - 4) + 3*" "+ "█\033[0m")
                    print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                    print("｜   " + "█" + "▄" * (taille_boite_commentaire - 2) + 4*"▄"+ "█\033[0m")
        else:
            print("\033[0;31m⚠ Il y a aucun posts pour le moment \033[0m")
        input()

    def comment_on_post(self):
        """
        Méthode pour commenter un post
        """
        if self.current_user:
            posts = self._database.get_posts()
            if not posts:
                print("\033[0;31m⚠ Aucun post disponible pour commenter.\033[0m")
                input()
            
            for i, post in enumerate(posts):
                print('\n')
                print(f"{i+1}.")
                print('\n')
                ligne_post = post.text.split('\n')
                taille_max_boite_dialogue = max(len(line) for line in ligne_post)
                taille_boite_dialogue = max(taille_max_boite_dialogue, len(post.user.username)) + 4
                print("\033[1;33m█" + "▀" * (taille_boite_dialogue - 2) + 4*"▀"+ "█\033[0m")
                print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
                print(f"\033[1;33m█   {post.user.username}" + " " * (taille_boite_dialogue - len(post.user.username) - 4) + 3*" "+ "█\033[0m")
                print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
                for ligne in ligne_post:
                    print(f"\033[1;33m█   {ligne}" + " " * (taille_boite_dialogue - len(ligne) - 4) + 3*" "+ "█\033[0m")
                print("\033[1;33m█" + " " * (taille_boite_dialogue - 2) + 3*" "+ " █\033[0m")
                print("\033[1;33m█" + "▄" * (taille_boite_dialogue - 2) + 4*"▄"+ "█\033[0m")
                
                for comment in post.comments:
                    print('\n')
                    ligne_comment = comment.text.split('\n')
                    taille_max_boite_commentaire = max(len(line) for line in ligne_comment)
                    taille_boite_commentaire = max(taille_max_boite_commentaire, len(comment.user.username)) + 4
                    print("｜   " + "█" + "▀" * (taille_boite_commentaire - 2) + 4*"▀"+ "█\033[0m")
                    print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                    print(f"｜   █   {comment.user.username}" + " " * (taille_boite_commentaire - len(comment.user.username) - 4) + 3*" "+ "█\033[0m")
                    print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                    for ligne in ligne_comment:
                        print(f"｜   █   {ligne}" + " " * (taille_boite_commentaire - len(ligne) - 4) + 3*" "+ "█\033[0m")
                    print("｜   " + "█" + " " * (taille_boite_commentaire - 2) + 3*" "+ " █\033[0m")
                    print("｜   " + "█" + "▄" * (taille_boite_commentaire - 2) + 4*"▄"+ "█\033[0m")


            post_index = int(input("Entrez le numéro du post que vous voulez commenter: ")) - 1
            if post_index < 0 or post_index >= len(posts):
                print("\033[0;31m⚠ Numéro de post invalide.\033[0m")
            print("\033[0;31m⚠ Entrée invalide.\033[0m")
            input()

            text = input("Entrez votre commentaire: ")
            selected_post = posts[post_index]
            self._database.add_comment(selected_post, self.current_user, text)
            print("\033[1;32mCommentaire ajouté avec succès !\033[0m")
        else:
            print("\033[0;31m⚠ Vous devez d'abord vous connecter.\033[0m")
        input()

# Class des commandes de l'application

class AppCmd(App):
    def run(self):
        while True:
            print('''
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█                                                                                         █
█\033[1;33m                                                                               \033[0m          █
█\033[1;33m                                                                               \033[0m          █
█\033[1;33m                                                                               \033[0m          █
█\033[1;33m                                                                               \033[0m          █
█\033[1;33m                    ████████╗██╗  ██╗██████╗ ███████╗ █████╗ ██████╗           \033[0m          █
█\033[1;33m                    ╚══██╔══╝██║  ██║██╔══██╗██╔════╝██╔══██╗██╔══██╗          \033[0m          █
█\033[1;33m                       ██║   ███████║██████╔╝█████╗  ███████║██║  ██║          \033[0m          █
█\033[1;33m                       ██║   ██╔══██║██╔══██╗██╔══╝  ██╔══██║██║  ██║          \033[0m          █
█\033[1;33m                       ██║   ██║  ██║██║  ██║███████╗██║  ██║██████╔╝          \033[0m          █
█\033[1;33m                       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝           \033[0m          █
█\033[1;33m                                                                               \033[0m          █
█\033[1;33m                               Le reseau social en terminal                    \033[0m          █
█\033[1;33m                                                                               \033[0m          █
█\033[1;33m                                  © Kaelian BAUDELET 2025                      \033[0m          █
█\033[1;33m                                                                               \033[0m          █
█\033[1;33m                                                                               \033[0m          █
█                                                                                         █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

            ''')
            login_user = self.current_user
            if login_user == None:
                print('Vous n\'etes pas connecté\n')
            else:
                print(f'Utilisateur actuellement connecté: {login_user}\n')

            print('1. Inscription')
            print('2. Connexion')
            print('3. Créer un post')
            print('4. Afficher un post aléatoire sur la plateforme')
            print('5. Afficher tous les posts')
            print('6. Commenter un post')
            print('7. Deconnexion')
            print('8. Quitter')

            choice = input('\nVeuillez choisir une option: ')
            if choice == '1':
                self.signup()
            elif choice == '2':
                self.login()
            elif choice == '3':
                self.create_post()
            elif choice == '4':
                self.display_random_post()
            elif choice == '5':
                self.display_posts()
            elif choice == '6':
                self.comment_on_post()
            elif choice == '7':
                self.disconnect()
            elif choice == '8':
                break
            else:
               print(chr(27) + "[2J")

# Demande du choix de base de donnée

while True:
    print('1. Utiliser une base de donnée en mémoire')
    print('2. Utiliser une base de donnée réelle (SQLite)')
    choice = input('Veuillez choisir une option: ')
    if choice == '1':
        app = AppCmd(InMemoryDatabase())
        break
    elif choice == '2':
        app = AppCmd(RealDatabase())
        break
    else:
        print(chr(27) + "[2J")

# Lancement de l'application
app.run()