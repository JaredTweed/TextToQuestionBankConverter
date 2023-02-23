# Created by: Jared Tweed

import tkinter as tk
from tkinter import *
from tkinter import filedialog
import customtkinter

import xml.etree.ElementTree as ET
import re
import datetime
import glob
import zipfile
import os
import sys
import shutil
import io

def write_time(root):
  """
  Add a 'CREATED' and 'UPDATED' element with the current time to the given root element.
  """
  time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')
  
  dates = ET.SubElement(root, 'DATES')
  created = ET.SubElement(dates, 'CREATED')
  created.set('value', time)
  updated = ET.SubElement(dates, 'UPDATED')
  updated.set('value', time)


def add_zip_to_name(zip_name):
  """
  Add the current time and a unique number to the given zip file name if a file with the same name already exists.
  """
  if(os.path.exists(f'{zip_name}.zip')):
    time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')

    if(os.path.exists(f'{zip_name}_{time}.zip')):
      file_iteration = 1
      iteration = str(file_iteration).zfill(5)
      while(os.path.exists(f'{zip_name}_{time}_{iteration}.zip')):
        file_iteration += 1
        iteration = str(file_iteration).zfill(5)
      zip_name = f'{zip_name}_{time}_{iteration}.zip'
    else:
      zip_name = f'{zip_name}_{time}.zip'
  else:
    zip_name = f'{zip_name}.zip'
  return zip_name


def create_manifest():
  """
  Create an 'imsmanifest.xml' file with default values.
  """
  xml_string = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="man00001"><organization default="toc00001"><tableofcontents identifier="toc00001"/></organization><resources><resource baseurl="res00001" file="res00001.dat" identifier="res00001" type="assessment/x-bb-pool"/></resources></manifest>'''
  root = ET.fromstring(xml_string)
  tree = ET.ElementTree(root)
  tree.write('imsmanifest.xml', encoding='utf-8', xml_declaration=True)


def text_to_xml_error_check(string):
  """
  Check the given text file for errors and exit if any are found.
  """
  # Question List
  numQuestions = len(re.findall(r'[^\s]+?\s*\n+\s*\n+\s*[^\s]+?', string))+1
  error = False

  error_screen.configure(state="normal")
  error_screen.delete("1.0", "end")
  
  lines = io.StringIO(string)#open(text_file, 'r')
  for i in range(numQuestions):
    thisLine = lines.readline()
    while(thisLine.isspace() or (thisLine.lower().startswith('mc') and thisLine[2:].isspace())):
      thisLine = lines.readline()

    # Scan the question for errors
    root = ET.Element('POOL')
    currentQ = ET.SubElement(root, 'QUESTION_MULTIPLECHOICE')
    body = ET.SubElement(currentQ, 'BODY')
    questionText = ET.SubElement(body, 'TEXT')
    questionText.text = thisLine.strip()
    
    # Scan the answers for errors
    a=0
    answerSelected = False
    multipleAnswersSelected = False 
    thisLine = lines.readline()
    while((not thisLine.isspace()) and thisLine != ''):
      a += 1
      thisLine = thisLine.strip()
      if(thisLine.startswith('*')):
        if(answerSelected):
          multipleAnswersSelected = True
        correct = a
        answerSelected = True
      thisLine = lines.readline()

    # Print error # tkinter --> tag_add(tag, i,j) method
    if (a == 0 or a == 1 or (not answerSelected) or multipleAnswersSelected or questionText.text.startswith('*')):
      if(a == 0):
        error_screen.insert("end", 'No answer options were provided for question {}.\n'.format(i+1))
      if(a == 1):
        error_screen.insert("end", 'Only one answer option was provided for question {}.\n'.format(i+1))
      if(not answerSelected):
        error_screen.insert("end", 'No answer is selected for question {}.\n'.format(i+1))
      if(multipleAnswersSelected):
        error_screen.insert("end", 'Multiple answers are selected for question {}.\n'.format(i+1))
      if(questionText.text.startswith('*')):
        error_screen.insert("end", "WARNING: Question {} begins with a '*' character.\n".format(i+1))
      error_screen.insert("end", '\n Question {}: '.format(i+1) + questionText.text + '\n\n\n')
      error = True

  # Quit program
  if(error):
    error_screen.insert("end", "Output file will not be produced. Fix input text and try again.\n")

  error_screen.configure(state="disabled")
  
  return error
    


def text_to_xml(text_file, xml_file, quiz_name):
  """
  Convert a text file with multiple choice questions to an XML file.
  Check for errors in the text file and exit if any are found.
 
  Args:
    text_file (str): Path to the text file to convert.
    xml_file (str): Path to the output XML file.
    quiz_name (str): The name of the quiz to include in the XML file.
  """

  # Open the text file and read its contents
  with open(text_file, 'r') as f:
    file = f.read()

  numQuestions = len(re.findall(r'[^\s]+?\s*\n+\s*\n+\s*[^\s]+?', file))+1
    
  # Create the root element
  root = ET.Element('POOL')
  course_id = ET.SubElement(root, 'COURSEID')
  course_id.set('value', 'IMPORT')
  title = ET.SubElement(root, 'TITLE')
  title.set('value', quiz_name)
  description = ET.SubElement(root, 'DESCRIPTION')
  text = ET.SubElement(description, 'TEXT')
  text.text = 'Created by the Blackboard Quiz Generator'
  write_time(root)

  # Question List
  qList = ET.SubElement(root, 'QUESTIONLIST')
  for i in range(numQuestions):
    q = ET.SubElement(qList, 'QUESTION')
    q.set('id', 'q{}'.format(i+1))
    q.set('class', 'QUESTION_MULTIPLECHOICE')

  # Open the text file for reading and iterate through each question
  lines = open(text_file, 'r')
  for i in range(numQuestions):
    # Skip blank or MC lines
    thisLine = lines.readline()
    while(thisLine.isspace() or (thisLine.lower().startswith('mc') and thisLine[2:].isspace())):
      thisLine = lines.readline()

    # Read the question text
    currentQ = ET.SubElement(root, 'QUESTION_MULTIPLECHOICE')
    currentQ.set('id', 'q{}'.format(i+1))
    write_time(currentQ)
    body = ET.SubElement(currentQ, 'BODY')
    
    questionText = ET.SubElement(body, 'TEXT')
    questionText.text = thisLine.strip()

    flags = ET.SubElement(body, 'FLAGS')
    flags.set('value', 'true')
    ishtml = ET.SubElement(flags, 'ISHTML')
    ishtml.set('value', 'true')
    isnewlineliteral = ET.SubElement(flags, 'ISNEWLINELITERAL')

    # Read the answer choices
    a=0
    answerSelected = False
    thisLine = lines.readline()
    while((not thisLine.isspace()) and thisLine != ''):
      a += 1
      
      answer = ET.SubElement(currentQ, 'ANSWER')
      answer.set('id', 'q{}_a{}'.format(i+1,a))
      answer.set('position', '{}'.format(a))
      write_time(answer)
      text = ET.SubElement(answer, 'TEXT')

      thisLine = thisLine.strip()
      if(thisLine.startswith('*')):
        thisLine = thisLine[1:]
        correct = a
        answerSelected = True
      text.text = thisLine

      thisLine = lines.readline()
      
    # Read and write the gradable answer
    if(not answerSelected):
      print('No answer is selected for question {}:'.format(i+1))
      print(questionText.text)
      input('Hit \'Enter\' to exit. Fix input text to create output.')
      sys.exit()
    grader = ET.SubElement(currentQ, 'GRADABLE')
    FWC = ET.SubElement(grader, 'FEEDBACK_WHEN_CORRECT')
    FWC.text = 'Good work'
    FWI = ET.SubElement(grader, 'FEEDBACK_WHEN_INCORRECT')
    FWI.text = 'That\'s not correct'

    correctA = ET.SubElement(grader, 'CORRECTANSWER')
    correctA.set('answer_id', 'q{}_a{}'.format(i+1,correct))

  # Create an ElementTree object and save it to the XML file
  tree = ET.ElementTree(root)
  ET.indent(tree, '  ')
  tree.write(xml_file, encoding="utf-8", xml_declaration=True)


def convert(): #string used to be text_file

  for tag in textbox.tag_names():
    textbox.tag_remove(tag, "1.0", "end")
  string = textbox.get("1.0", "end")

  print(string)

  # Assign the input file to 'text_file'
  text_to_xml_error_check(string)

  # Get the quiz name from the user
  print("Note, file names cannot include any of the following characters:\n  \/:*?\"<>|")
  if(quizName.get() != ''):
    QuizName = quizName.get()
  else:
    QuizName = 'Quiz'
  

##  # Check if any character in QuizName is in \/:*?"<>|
##  c = ':'
##  nameIsValid = True
##  for char in QuizName:
##    if char in "\/:*?\"<>|":
##      nameIsValid = False
##      c = char
##  while(not nameIsValid):
##    print(f"'{c}' is not allowed in a file name.")
##    QuizName = input("Enter a valid name for your quiz: ")
##    nameIsValid = True
##    for char in QuizName:
##      if char in "\/:*?\"<>|":
##        nameIsValid = False
##        c = char

        
##  # Check if a zip file with the same name already exists
##  x = 'q'
##  if(os.path.exists(f'{QuizName}.zip')):
##    print("Because a zip file with that name already exists, the new output file")
##    print("will have the same name with the date and time appended to the end of")
##    print("its title. Press 'Enter' to accept. If you wish to replace the prior")
##    x = input("output file instead, type 'r' then hit 'Enter'.\n\n")
##
##  # Create zipped files
##  text_to_xml(text_file, 'res00001.dat', QuizName)
##  create_manifest()
##
##  # Zip the XML and manifest files into a folder with a proper name
##  if(x.lower() == 'r'):
##    zipFileName = f'{QuizName}.zip'
##  else:
##    zipFileName = add_zip_to_name(QuizName)
##  with zipfile.ZipFile(zipFileName, 'w') as zip:
##    zip.write('imsmanifest.xml')
##    zip.write('res00001.dat')
##
##  # Delete the unzipped XML and manifest files
##  try:
##    os.remove('imsmanifest.xml')
##    os.remove('res00001.dat')
##  except OSError:
##    pass
##
##  # renames input file
##  new_name = 'converted ' + text_file[8:]
##  if(os.path.exists(new_name)):
##    print(f"The input file\n'{new_name}'\nalready has a converted file with the same name. Type 'r' then hit 'Enter'")
##    print("if you wish to replace it. Otherwise hit 'Enter', and the input text")
##    r = input("file will have its time and date appended to the end of its name.\n\n")
##    if(r.lower() == 'r'):
##      try:
##        os.remove(new_name)
##      except OSError:
##        pass    
##    else:
##      time_now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
##      new_name = f'{new_name[:-4]}_{time_now}.txt'
##  try:
##    shutil.copy(text_file, new_name)
##    os.remove(text_file)
##  except:
##    print("ERROR. Could not rename input text file because it is being")
##    print("used somewhere else (likely in a terminal or in another instance")
##    print("of this program). Instead another copy of the input text file")
##    input("was made and renamed. Please delete original copy manually.")












def index_to_ctk(string, index):
  custom_index = "{}.{}".format(string.count('\n', 0, index) + 1, index - string.rfind('\n', 0, index))
  return custom_index

def find_last_regex_match(string):
  regex = r'\s'

  # Make a list of whitespace indices
  indices = []
  for match in re.finditer(regex, string):
    indices.extend(range(match.start(), match.end()))
  
    # If there are no matches, return None
  if len(indices) == 0:
    return -1

  if(string[indices[-1]] == '\n'):
    return indices[-1]+1

  # if the last character of the string is a whitespace character
  if(len(string) - 1 == indices[-1]):
    # return the last non-consecutive index
    indices.reverse()
    for i in range(len(indices)):
      if(i+1 == len(indices)):
        return 0
      if(indices[i] - indices[i+1] != 1):
        return indices[i+1]+1
  # if the last character of the string is not a whitespace character
  else:
    return indices[-1]+1

def textbox_ctrl_backspace(event):
  ent = event.widget
  end_idx = ent.index(tk.INSERT)

  string = ent.get("1.0", end_idx)
  index = find_last_regex_match(string)
  
  if index != -1:
    custom_index = index_to_ctk(string, index)
    ent.delete(custom_index,end_idx)
  else:
    ent.delete("0.0",end_idx)

def entry_ctrl_backspace(event):
  ent = event.widget
  end_idx = ent.index(tk.INSERT)

  string = ent.get()
  string = string[:end_idx]
  index = find_last_regex_match(string)+1
  
  if index != -1:
    ent.delete(index,end_idx)
  else:
    ent.delete("0.0",end_idx)


def save_text_to_file(event=0):
  # Get the text from the textbox
  text = textbox.get("1.0", "end")

  # Write the text to the chosen file
  if(text != ''):
    # Open a file dialog to choose the file path and name to save to
    file_path = filedialog.asksaveasfilename(initialfile=quizName.get(), defaultextension=".txt", filetypes=[("text file", "*.txt")])

    with open(file_path, "w") as file:
      file.write(text)

def update_linenumbers(event):
  root.after(1, _update_linenumbers)

def _update_linenumbers():
  
  i = textbox.index(tk.INSERT)
  cursor_pos = textbox.index("insert")
  line_num = cursor_pos.split('.')[0]

  cursor_index = textbox.index("insert")
  cursor_index = "{}.{}".format(cursor_index.split('.')[0], str(int(cursor_index.split('.')[1])+1))
  string = textbox.get("1.0",cursor_index)
  numQuestions = len(re.findall(r'[^\s]+?\s*\n+\s*\n+\s*[^\s]+?', string))+1
  
  linenumbers.configure(text=f"Line Number: {line_num}\nQuestion Number: {numQuestions}")

# Main Code

root = customtkinter.CTk()
root.geometry("920x400")
root.resizable(True, True)
root.minsize(920, 400)
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")

root.grid_rowconfigure((0), weight=0)
root.grid_rowconfigure((2), weight=2)
root.grid_columnconfigure(1, weight=1, minsize=240)
root.grid_columnconfigure(3, minsize=310)

root.bind('<Control-s>', save_text_to_file)

title = Label(master=root, text="Text To Question Bank Converter", fg="white", background="#222325", font=("Bahnschrift", 20))
title.grid(row=0, column=0, padx=10, pady=10, sticky="n", columnspan = 3)

quizName = customtkinter.CTkEntry(root, placeholder_text="Quiz Name", font=("Bahnschrift", 20),width=300,height=30,border_width=1,corner_radius=10)
quizName.grid(row=1, column=0, padx=(10, 2), pady=5, sticky="ew", columnspan = 2)
quizName.bind('<Control-BackSpace>', entry_ctrl_backspace)

quizNameConstraints = Label(master=root, text="Note, file names cannot include any of\n the following characters:\t  \ /:*?\"<>|", fg="white", background="#222325", font=("Bahnschrift", 10))
quizNameConstraints.grid(row=1, column=2, padx=(2,10), pady=10, sticky="w")

textbox = customtkinter.CTkTextbox(master=root, width=400, height=600, font=("Bahnschrift", 15), corner_radius=10, wrap='word')
textbox.grid(row=2, column=0, padx=(10,2), pady=10, sticky="nsew", columnspan = 3)
textbox.focus_set()
textbox.bind('<Control-BackSpace>', textbox_ctrl_backspace)

textbox.bind("<Key>", update_linenumbers)
textbox.bind("<MouseWheel>", update_linenumbers)
textbox.bind("<Configure>", update_linenumbers)

##linenumbers = customtkinter.CTkTextbox(master=root, width=60, height=600, font=("Bahnschrift", 15), corner_radius=10, state="disabled", activate_scrollbars=False)
##linenumbers.grid(row=2, column=0, padx=(10, 1), pady=10, sticky="w")

error_screen = customtkinter.CTkTextbox(master=root, width=200, height=600, font=("Bahnschrift", 15), corner_radius=10, state="normal", wrap='word')
error_screen.grid(row=1, column=3, padx=(2, 10), pady=10, sticky="nsew", rowspan=3)
error_screen.insert("end", "Error explanations for the input text will go here if question bank creation fails.")
error_screen.configure(state="disabled")

linenumbers = Label(master=root, text="Line Number: 1\nQuestion Number: 1", fg="white", background="#222325", font=("Bahnschrift", 10), anchor="w")
linenumbers.grid(row=3, column=0, sticky="ew", padx=(10,2), pady=10, columnspan = 1)

saveTxtButton = customtkinter.CTkButton(master=root, text="Save Textbox As Textfile", width=250, font=("Bahnschrift", 20), command=save_text_to_file)
saveTxtButton.grid(row=3, column=1, sticky="ew", padx=(2,2), pady=10, columnspan = 1)

questionBankButton = customtkinter.CTkButton(master=root, text="Create Question Bank", width=100, font=("Bahnschrift", 20), command=convert)
questionBankButton.grid(row=3, column=2, sticky="ew", padx=(2,5), pady=10, columnspan = 1)


root.mainloop()
