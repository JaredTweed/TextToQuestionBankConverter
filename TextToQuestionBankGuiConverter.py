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
import webbrowser

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
  numQuestions = len(re.findall(r'[^\s]+?\s*\n+\s*\n+\s*[mc\s*\n+\s*\n+\s*]*(?=[^\s]+?)', string, re.IGNORECASE))+1
  error = False
  currentLineNumber = 0

  error_screen.configure(state="normal")

  if(string.isspace() == True or string == textbox.placeholder+'\n'):
    error_screen.insert("end", 'No text is provided to convert.\n\n')
    error = True
  else:
    lines = io.StringIO(string)
    for i in range(numQuestions):
      thisLine = lines.readline()
      currentLineNumber += 1
      
      while(thisLine.isspace() or (thisLine.lower().startswith('mc') and thisLine[2:].isspace())):
        thisLine = lines.readline()
        currentLineNumber += 1

      # Scan the question for errors
      root = ET.Element('POOL')
      currentQ = ET.SubElement(root, 'QUESTION_MULTIPLECHOICE')
      body = ET.SubElement(currentQ, 'BODY')
      questionText = ET.SubElement(body, 'TEXT')
      questionText.text = thisLine.strip()

      highlight_start = currentLineNumber
      
      # Scan the answers for errors
      a=0
      answerSelected = False
      multipleAnswersSelected = False 
      thisLine = lines.readline()
      currentLineNumber += 1
      while((not thisLine.isspace()) and thisLine != ''):
        a += 1
        thisLine = thisLine.strip()
        if(thisLine.startswith('*')):
          if(answerSelected):
            multipleAnswersSelected = True
          correct = a
          answerSelected = True
        thisLine = lines.readline()
        currentLineNumber += 1
      highlight_end = currentLineNumber

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
        error_screen.insert("end", 'Question {}: '.format(i+1) + questionText.text + '\n\n\n')
        error = True

        textbox.tag_add("start", f"{highlight_start}.0", f"{highlight_end}.0")
        textbox.tag_config("start", background= "dark red", foreground= "white")
        error_line_numbers.append(f"{highlight_start}.99")

  # Quit program
  if(error):
    error_screen.insert("end", "Output file will not be produced. Fix input text and try again.\n")

  error_screen.configure(state="disabled")
  
  return error
    


def text_to_xml(string, xml_file, quiz_name):
  """
  Convert a text file with multiple choice questions to an XML file.
  Check for errors in the text file and exit if any are found.
 
  Args:
    string (str): The contents of the text box which will convert.
    xml_file (str): Path to the output XML file.
    quiz_name (str): The name of the quiz to include in the XML file.
  """

  # Open the text file and read its contents
  numQuestions = len(re.findall(r'[^\s]+?\s*\n+\s*\n+\s*[mc\s*\n+\s*\n+\s*]*(?=[^\s]+?)', string, re.IGNORECASE))+1
    
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
  lines = io.StringIO(string)
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


def check_all_errors():
  search.instance = 0
  search.prevPattern = ''
  search.iteratingQuestions = False
  global error_line_numbers
  error_line_numbers.clear()
  textbox.tag_remove("start", "1.0", "end")
  string = textbox.get("1.0", "end")

  # Delete error messages from previous conversion attempts
  error_screen.configure(state="normal")
  error_screen.delete("1.0", "end")
  error_screen.configure(state="disabled")

  # Get the quiz name from the user
  if(quizName.get() != ''):
    QuizName = quizName.get()
  else:
    QuizName = 'Quiz'

  # Check if any character in QuizName is in \/:*?"<>| 
  error_screen.configure(state="normal")
  c = []
  nameIsValid = True
  for char in QuizName:
    if char in "\/:*?\"<>|":
      nameIsValid = False
      if(char not in c): c.append(char)
  if (nameIsValid == False):
    for item in c: error_screen.insert("end", f"'{item}' is not allowed in a quiz name.\n")
    error_screen.insert("end", "Enter a valid name for your quiz.\n\n\n")
  error_screen.configure(state="disabled")

  # Check for errors in the textbox
  hasError = text_to_xml_error_check(string)

  return hasError == False and nameIsValid

def convert():

  errors_present = check_all_errors()

  # Create the question bank
  if(errors_present and textbox.get("1.0", "end") != '' and textbox.get("1.0", "end") != textbox.placeholder+'\n'):
    
    # Choose a location for the zip file
    file_path = filedialog.asksaveasfilename(initialfile=quizName.get(), defaultextension=".zip", filetypes=[("zip file", "*.zip")])
    with zipfile.ZipFile(file_path, 'w') as zip_file:
      pass
    file_name = os.path.basename(file_path)

    # Create the files for the zip folder
    string = textbox.get("1.0","end")
    QuizName = quizName.get()
    text_to_xml(string, 'res00001.dat', QuizName)
    create_manifest()

    # Zip the XML and manifest files into a folder with a proper name
    with zipfile.ZipFile(file_path, 'w') as zip:
      zip.write('imsmanifest.xml')
      zip.write('res00001.dat')

    # Delete the unzipped XML and manifest files
    try:
      os.remove('imsmanifest.xml')
      os.remove('res00001.dat')
    except OSError:
      pass

    error_screen.configure(state="normal")
    error_screen.insert("end", "Zip file created.\n")
    error_screen.configure(state="disabled")













def index_to_ctk(string, index):
  custom_index = "{}.{}".format(string.count('\n', 0, index) + 1, index - string.rfind('\n', 0, index)-1) 
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
    index += 1
    custom_index = index_to_ctk(string, index)
    ent.delete(custom_index,end_idx)
  else:
    ent.delete("0.0",end_idx)
  delay_update_linenumbers()

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
  delay_update_linenumbers()

def save_text_to_file(event=None):
  # Get the text from the textbox
  text = textbox.get("1.0", "end")

  # Write the text to the chosen file
  if(text != ''):
    # Open a file dialog to choose the file path and name to save to
    file_path = filedialog.asksaveasfilename(initialfile=quizName.get(), defaultextension=".txt", filetypes=[("text file", "*.txt")])

    with open(file_path, "w") as file:
      file.write(text)

def open_textfile():
  file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("text file", "*.txt")])
  with open(file_path, "r") as file:
      text = file.read()
  # Do something with the text, such as display it in a text box
  textbox.delete("1.0", "end")
  textbox.configure(text_color='white')
  textbox.insert("1.0", text)

def delay_update_linenumbers(event=None):
  # This delays the line number update until the cursor has already moved.
  root.after(1, update_linenumbers)

def update_linenumbers(event=None, cursor_index=None):
  if(cursor_index == None):
    cursor_index = textbox.index("insert")
    cursor_index = "{}.{}".format(cursor_index.split('.')[0], str(int(cursor_index.split('.')[1])+1))
  line_num = cursor_index.split('.')[0]
  string = textbox.get("1.0",cursor_index)
  numQuestions = len(re.findall(r'[^\s]+?\s*\n+\s*\n+\s*[mc\s*\n+\s*\n+\s*]*(?=[^\s]+?)', string, re.IGNORECASE))+1
  
  linenumbers.configure(text=f"Line: {line_num}\nQn: {numQuestions}")

def on_textbox_focusin(event):
  if textbox.get("0.0", "end") == textbox.placeholder+'\n':
    textbox.delete("0.0", "end")
    textbox.configure(text_color='white')

def on_textbox_focusout(event):
  if textbox.get("0.0", "end") == '\n':
    textbox.insert("0.0", textbox.placeholder)
    textbox.configure(text_color='grey')

def open_instructions():
  webbrowser.open("https://github.com/JaredTweed/TextToQuestionBankConverter#readme")

def fontsize_1(event):
  size = 5
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def fontsize_2(event):
  size = 10
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def fontsize_3(event):
  size = 15
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def fontsize_4(event):
  size = 20
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def fontsize_5(event):
  size = 25
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def fontsize_6(event):
  size = 30
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def fontsize_7(event):
  size = 35
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def fontsize_8(event):
  size = 40
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def fontsize_9(event):
  size = 50
  textbox.configure(font=("Bahnschrift", size))
  error_screen.configure(font=("Bahnschrift", size))

def escape_regex(text):
  special_chars = ['\\', '.', '*', '+', '?', '{', '}', '[', ']', '|', '(', ')', '^', '$']
  pattern = '|'.join(re.escape(char) for char in special_chars)
  return re.sub(pattern, lambda match: '\\' + match.group(0), text)


def highlight_instance(pattern, instance):
  textbox.tag_remove("search tag", "1.0", "end")
  instance_interval = []

  matches = re.finditer(pattern, textbox.get("0.0", "end"), re.IGNORECASE)
  i = 0
  if(matches != None):
    for match in matches:
      instance_interval.append([match.start(), match.end()])
      i += 1
  if(i != 0):
    tkinter_index_start = index_to_ctk(textbox.get("0.0", "end"), instance_interval[instance % i][0])
    tkinter_index_end = index_to_ctk(textbox.get("0.0", "end"), instance_interval[instance % i][1])

    textbox.see(index_to_ctk(textbox.get("0.0", "end"), instance_interval[instance % i][0]))

    textbox.tag_add("search tag", tkinter_index_start, tkinter_index_end)
    textbox.tag_config("search tag", background= "orange", foreground= "white")

    update_linenumbers(cursor_index=tkinter_index_end)


def search_text(event):
  root.after(1, _search_text)

def _search_text():
  search.iteratingQuestions = False
  pattern = escape_regex(search.get())
  if(pattern == search.prevPattern and pattern != ''):
    search.instance += 1
  else:
    search.instance = 0
    search.prevPattern = pattern
  root.after(2, lambda: highlight_instance(pattern, search.instance))
  textbox.tag_raise("search tag")

def iterate_wrong_questions(event):
  if(len(error_line_numbers) != 0):
    textbox.tag_remove("search tag", "1.0", "end")
    if(search.iteratingQuestions == True):
      search.instance += 1
    else:
      search.instance = 0
      search.iteratingQuestions = True
      search.prevPattern = ''
    question_index = error_line_numbers[search.instance % len(error_line_numbers)]
    textbox.see(question_index)
    update_linenumbers(cursor_index=question_index)
    textbox.tag_raise("search tag")

def show_search_entry(event):
  search.grid(row=1, column=3, padx=(2,2), pady=(10,2), sticky="ew")
  search.focus()
  search.select_range("0", "end")
  check_all_errors()

def hide_search(event):
  textbox.tag_remove("search tag", "1.0", "end")
  search.grid_forget()


# Main Code

error_line_numbers = []

root = customtkinter.CTk()
root.geometry("800x400")
root.resizable(True, True)
root.minsize(800, 400)
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")

root.grid_rowconfigure((0), weight=0)
root.grid_rowconfigure((2), weight=2)
root.grid_rowconfigure((3,4), weight=0)
root.grid_columnconfigure(1, minsize=190)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(4, weight=2)

root.bind('<Control-s>', save_text_to_file)
root.bind('<Control-f>', show_search_entry)

root.bind('<Control-KeyPress-1>', fontsize_1)
root.bind('<Control-KeyPress-2>', fontsize_2)
root.bind('<Control-KeyPress-3>', fontsize_3)
root.bind('<Control-KeyPress-4>', fontsize_4)
root.bind('<Control-KeyPress-5>', fontsize_5)
root.bind('<Control-KeyPress-6>', fontsize_6)
root.bind('<Control-KeyPress-7>', fontsize_7)
root.bind('<Control-KeyPress-8>', fontsize_8)
root.bind('<Control-KeyPress-9>', fontsize_9)
root.bind('<Control-KeyPress-0>', fontsize_1)

# Row 0

title = Label(master=root, text="Text To Question Bank Converter", fg="white", background="#222325", font=("Bahnschrift", 20))
title.grid(row=0, column=0, padx=10, pady=10, sticky="n", columnspan = 4)

help_button = customtkinter.CTkButton(master=root, text="Help", font=("Bahnschrift", 20), command=open_instructions)
help_button.grid(row=0, column=4, padx=(2,10), pady=(10,5), sticky="nsew", columnspan = 1)


# Row 1

quizName = customtkinter.CTkEntry(root, placeholder_text="Quiz Name", font=("Bahnschrift", 20),width=300,height=30,border_width=1,corner_radius=10)
quizName.grid(row=1, column=0, padx=(10, 2), pady=(10,2), sticky="ew", columnspan = 3)
quizName.bind('<Control-BackSpace>', entry_ctrl_backspace)

quizNameConstraints = Label(master=root, text="Quiz names cannot include\n the following:\t\ /:*?\"<>|", fg="white", background="#222325", font=("Bahnschrift", 10))
quizNameConstraints.grid(row=1, column=3, padx=(2,2), pady=(10,2), sticky="w")

search = customtkinter.CTkEntry(root, placeholder_text="Search", font=("Bahnschrift", 20),width=80,height=30,border_width=1,corner_radius=10)
search.instance = 0
search.prevPattern = ''
search.iteratingQuestions = False
search.bind("<Return>", search_text)
search.bind("<FocusOut>", hide_search)
search.bind("<Control-Return>", iterate_wrong_questions)

# Row 2

textbox = customtkinter.CTkTextbox(master=root, font=("Bahnschrift", 15), corner_radius=10, wrap='word')

textbox.grid(row=2, column=0, padx=(10,2), pady=(2,2), sticky="nsew", columnspan = 4)
textbox.bind('<Control-BackSpace>', textbox_ctrl_backspace)

textbox.bind("<Key>", delay_update_linenumbers)
textbox.bind("<Button>", delay_update_linenumbers)

textbox.placeholder = 'Paste your text here'
textbox.insert("0.0", textbox.placeholder)
textbox.configure(text_color='grey')
textbox.bind('<FocusIn>', on_textbox_focusin)
textbox.bind('<FocusOut>', on_textbox_focusout)

error_screen = customtkinter.CTkTextbox(master=root, width=200, height=600, font=("Bahnschrift", 15), corner_radius=10, state="normal", wrap='word')
error_screen.grid(row=1, column=4, padx=(2, 10), pady=10, sticky="nsew", rowspan=4)
error_screen.insert("end", "Error explanations for the input text will go here if question bank creation fails.")
error_screen.configure(state="disabled")

# Row 3 & 4

linenumbers = Label(master=root, text="Line: 1\nQn: 1", fg="white", background="#222325", font=("Bahnschrift", 20), anchor="w")
linenumbers.grid(row=3, column=0, sticky="ew", padx=(10,2), pady=(2,10), rowspan = 2, columnspan = 1)

saveTxtButton = customtkinter.CTkButton(master=root, text="Save Textbox As Textfile", width=250, font=("Bahnschrift", 20), command=save_text_to_file)
saveTxtButton.grid(row=3, column=1, sticky="nsew", padx=(2,2), pady=(2,2), columnspan = 1)

openTxtButton = customtkinter.CTkButton(master=root, text="Open Textfile", font=("Bahnschrift", 20), command=open_textfile)
openTxtButton.grid(row=4, column=1, sticky="nsew", padx=(2,2), pady=(2,10), columnspan = 1)

questionBankButton = customtkinter.CTkButton(master=root, text="Create Question Bank", width=100, font=("Bahnschrift", 20), command=convert)
questionBankButton.grid(row=3, column=2, sticky="nsew", padx=(2,2), pady=(2,10), rowspan = 2, columnspan = 2)

root.mainloop()
