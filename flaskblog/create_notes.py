import pandas as pd
from collections import OrderedDict
import datetime
import os
from flask import Flask
from models import User, Tag, Note, Interaction

# notes = [{'time':datetime.datetime.now(),'id':100,'userid':6,'content':' Class : A collection of fields (instance and class variables) and methods. Instance variable: An instance variable is a variable that is defined in a class, but outside of a method. There is one copy of the variable for every instance (object) created from that class. Class variable: A class variable or static variable is defined in a class, but there is only one copy regardless of how many objects are created from that class'},
# {'time':datetime.datetime.now(),'id':101,'userid':6,'content':'If statement: The purpose of the if statement is to make decisions, and execute different parts of your program depending on a boolean true/false value. About 99% of the flow decisions are made with if. [The other 1% of the decisions use the switch statement.'},
# {'time':datetime.datetime.now(),'id':102,'userid':7,'content':'For loop: The for statement is similar to the while statement, but it is often easier to use if you are counting or indexing because it combines three elements of many loops: initialization, testing, and incrementing. '},
# {'time':datetime.datetime.now(),'id':103,'userid':6,'content':'While loop:The purpose of the while statement is to repeat a group of Java statements many times. Its written just like an if statement, except that it uses the while keyword.'},
# {'time':datetime.datetime.now(),'id':104,'userid':8,'content':'Exceptions: When your program causes an error, Java throws an exception. Java then throws this exception to a part of the program that will catch it You shouldnt try to catch most exceptions, but you should catch all exceptions that are caused by events which you have no control over - exceptions caused by bad user input or I/O problems. '},
# {'time':datetime.datetime.now(),'id':105,'userid':6,'content':'Constructors:When you create a new instance (a new object) of a class using the new keyword, a constructor for that class is called. Constructors are used to initialize the instance variables (fields) of an object. Constructors are similar to methods, but with some important differences. Constructor name is class name. A constructors must have the same name as the class its in. Default constructor. If you don\'t define a constructor for a class, a default parameterless constructor is automatically created by the compiler. The default constructor calls the default parent constructor (super()) and initializes all instance variables to default value (zero for numeric types, null for object references, and false for booleans)'},
# {'time':datetime.datetime.now(),'id':106,'userid':8,'content':'Float : Floating-point numbers are like real numbers in mathematics, for example, 3.14159, -0.000001. Java has two kinds of floating-point numbers: float and double, both stored in IEEE-754 format. The default type when you write a floating-point literal is double. '},
# {'time':datetime.datetime.now(),'id':107,'userid':8,'content':'Integers : Integers are whole numbers, for example, -35, 0, 2048, .... Integers are represented in binary inside the computer, and in decimal in Java source programs. Java automatically converts decimal numbers you write in your source program into binary numbers internally. '},
# {'time':datetime.datetime.now(),'id':108,'userid':8,'content':'Variables : Variables are places in memory to store values. There are different kinds of variables, and every language offers slightly different characteristics.Scope of a variable is who can see it. The scope of a variable is related program structure: eg, block, method, class, package, child class.Lifetime is the interval between the creation and destruction of a variable. The following is basically how things work in Java. Local variables and parameters are created when a method is entered and destroyed when the method returns. Instance variables are created by new and destroyed when there are no more references to them. Class (static) variables are created when the class is loaded and destroyed when the program terminates.'},
# {'time':datetime.datetime.now(),'id':109,'userid':5,'content':' Class : A collection of fields (instance and class variables) and methods. Instance variable: An instance variable is a variable that is defined in a class, but outside of a method. There is one copy of the variable for every instance (object) created from that class. Class variable: A class variable or static variable is defined in a class, but there is only one copy regardless of how many objects are created from that class'},
# {'time':datetime.datetime.now(),'id':110,'userid':9,'content':'If statement: The purpose of the if statement is to make decisions, and execute different parts of your program depending on a boolean true/false value. About 99% of the flow decisions are made with if. [The other 1% of the decisions use the switch statement.'},
# {'time':datetime.datetime.now(),'id':111,'userid':7,'content':'For loop: The for statement is similar to the while statement, but it is often easier to use if you are counting or indexing because it combines three elements of many loops: initialization, testing, and incrementing. '},
# {'time':datetime.datetime.now(),'id':112,'userid':6,'content':'While loop:The purpose of the while statement is to repeat a group of Java statements many times. Its written just like an if statement, except that it uses the while keyword.'},
# {'time':datetime.datetime.now(),'id':113,'userid':8,'content':'Exceptions: When your program causes an error, Java throws an exception. Java then throws this exception to a part of the program that will catch it You shouldnt try to catch most exceptions, but you should catch all exceptions that are caused by events which you have no control over - exceptions caused by bad user input or I/O problems. '},
# {'time':datetime.datetime.now(),'id':114,'userid':6,'content':'Constructors:When you create a new instance (a new object) of a class using the new keyword, a constructor for that class is called. Constructors are used to initialize the instance variables (fields) of an object. Constructors are similar to methods, but with some important differences. Constructor name is class name. A constructors must have the same name as the class its in. Default constructor. If you don\'t define a constructor for a class, a default parameterless constructor is automatically created by the compiler. The default constructor calls the default parent constructor (super()) and initializes all instance variables to default value (zero for numeric types, null for object references, and false for booleans)'},
# {'time':datetime.datetime.now(),'id':115,'userid':8,'content':'Float : Floating-point numbers are like real numbers in mathematics, for example, 3.14159, -0.000001. Java has two kinds of floating-point numbers: float and double, both stored in IEEE-754 format. The default type when you write a floating-point literal is double. '},
# {'time':datetime.datetime.now(),'id':116,'userid':8,'content':'Integers : Integers are whole numbers, for example, -35, 0, 2048, .... Integers are represented in binary inside the computer, and in decimal in Java source programs. Java automatically converts decimal numbers you write in your source program into binary numbers internally. '},
# {'time':datetime.datetime.now(),'id':117,'userid':9,'content':'Variables : Variables are places in memory to store values. There are different kinds of variables, and every language offers slightly different characteristics.Scope of a variable is who can see it. The scope of a variable is related program structure: eg, block, method, class, package, child class.Lifetime is the interval between the creation and destruction of a variable. The following is basically how things work in Java. Local variables and parameters are created when a method is entered and destroyed when the method returns. Instance variables are created by new and destroyed when there are no more references to them. Class (static) variables are created when the class is loaded and destroyed when the program terminates.'}
# ]

# notes_df = pd.DataFrame(notes)
# #print(notes_df.head(2))

# interactions_d = [{'time':datetime.datetime.now(),'eventType':'VIEW','id':100,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':101,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'VIEW','id':102,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':103,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'VIEW','id':104,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':105,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'BOOKMARK','id':106,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':107,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':108,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':109,'userid':5},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':110,'userid':8},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':111,'userid':8},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':112,'userid':7},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':113,'userid':6},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':114,'userid':6},
# {'time':datetime.datetime.now(),'eventType':'BOOKMARK','id':115,'userid':9},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':116,'userid':9},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':115,'userid':7},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':112,'userid':7},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':117,'userid':7},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':111,'userid':7},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':111,'userid':6},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':112,'userid':6},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':110,'userid':6},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':115,'userid':9},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':112,'userid':9},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':117,'userid':9},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':111,'userid':9},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':110,'userid':8},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':111,'userid':8},
# {'time':datetime.datetime.now(),'eventType':'FOLLOW','id':116,'userid':8},
# {'time':datetime.datetime.now(),'eventType':'LIKE','id':112,'userid':8}
# ]
# interactions_df = pd.DataFrame(interactions_d)

curr_d = os.getcwd()
data= os.path.join(curr_d,'articles-sharing-and-reading-from-ci-t-deskdrop')
notes_f = os.path.join(data,'shared_articles.csv')
interactions_f = os.path.join(data,'users_interactions.csv')
def get_notes_df():
	#notes_df = pd.read_csv(notes_f)
	notes = Note.query.all()
	notes_list = []
	for note in notes:
		d = {}
		d['contentId'] = note.id
		d['authorPersonId'] = note.user_id
		d['title'] = note.title
		d['text'] = note.content
		notes_list.append(d)
	notes_df = pd.DataFrame(notes_list)
	return notes_df
def get_interactions_df():
	interactions = Interaction.query.all()
	inters = []
	for i in interactions:
		d = {}
		d['contentId'] = i.note_id
		d['personId'] = i.user_id
		d['eventType'] = i.event
		inters.append(d)
	interactions_df = pd.DataFrame(inters)
	return interactions_df





