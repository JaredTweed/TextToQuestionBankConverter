# Created by: Jared Tweed

import xml.etree.ElementTree as ET
import re
import datetime
import glob
import zipfile
import os
import sys

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
    time = datetime.datetime.utcnow().strftime('%Y-%m-%d_%H-%M')

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

def text_to_xml_error_check(text_file):
  """
  Check the given text file for errors and exit if any are found.
  """
  with open(text_file, 'r') as f:
    file = f.read()

  #QuestionList
  numQuestions = len(re.findall(r'[^\s]+\s*\n+\s*\n+\s*[^\s]+', file))+1
  
  lines = open(text_file, 'r')
  for i in range(numQuestions):
    thisLine = lines.readline()
    while(thisLine.isspace() or (thisLine.lower().startswith('mc') and thisLine[2:].isspace())):
      thisLine = lines.readline()

    #Question
    root = ET.Element('POOL')
    currentQ = ET.SubElement(root, 'QUESTION_MULTIPLECHOICE')
    body = ET.SubElement(currentQ, 'BODY')
    questionText = ET.SubElement(body, 'TEXT')
    questionText.text = thisLine.strip()
    
    #Answer
    a=0
    answerSelected = False
    thisLine = lines.readline()
    while(not thisLine.isspace()):
      a += 1
      thisLine = thisLine.strip()
      if(thisLine.startswith('*')):
        correct = a
        answerSelected = True
      thisLine = lines.readline()
      
    #Gradable
    if(not answerSelected):
      print('No answer is selected for question {}:'.format(i+1))
      print(questionText.text)
      input('Hit \'Enter\' to exit. Fix input text to create output.')
      sys.exit()


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

  numQuestions = len(re.findall(r'[^\s]+\s*\n+\s*\n+\s*[^\s]+', file))+1
    
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

  #QuestionList
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
    while(not thisLine.isspace()):
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




# Main

# Assign the input file to 'text_file'
text_file = glob.glob('convert *.txt')

# Check for errors
if len(text_file) > 1:
  print('ERROR, more than 1 convert file')
  print('Below are the given convert files')
  for i in text_file:
    print(i)
  input('ERROR, more than 1 convert file')
  sys.exit()
elif len(text_file) == 0:
  print("ERROR. No file to convert. The program converts any '.txt' file in the")
  input("same directory which has a filename starting with 'convert '.")
  sys.exit()
else:
  text_file = text_file[0]
text_to_xml_error_check(text_file)

# Get the quiz name from the user
QuizName = input("Enter the name of your quiz: ")

# Check if a zip file with the same name already exists
x = 'q'
if(os.path.exists(f'{QuizName}.zip')):
  print("Because the zip file already exists, the new one will have the new")
  print("name appended to the end of its title. Press 'Enter' to accept. If")
  x = input("you wish to replace the current instead, type 'r' then hit 'Enter'.\n")

# Create zipped files
text_to_xml(text_file, 'res00001.dat', QuizName)
create_manifest()

# Zip the XML and manifest files into a folder with a proper name
if(x.lower == 'r'):
  zipFileName = f'{QuizName}.zip'
else:
  zipFileName = add_zip_to_name(QuizName)
  
with zipfile.ZipFile(zipFileName, 'w') as zip:
  zip.write('imsmanifest.xml')
  zip.write('res00001.dat')

# Delete the unzipped XML and manifest files
try:
  os.remove('imsmanifest.xml')
  os.remove('res00001.dat')
except OSError:
  pass

# renames input file
new_name = 'converted ' + text_file[8:]
os.rename(text_file, new_name)


