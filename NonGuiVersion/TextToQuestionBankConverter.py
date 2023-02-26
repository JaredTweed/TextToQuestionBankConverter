# Created by: Jared Tweed

import xml.etree.ElementTree as ET
import re
import datetime
import glob
import zipfile
import os
import sys
import shutil

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

def text_to_xml_error_check(text_file):
  """
  Check the given text file for errors and exit if any are found.
  """
  with open(text_file, 'r') as f:
    file = f.read()

  # Question List
  numQuestions = len(re.findall(r'[^\s]+?\s*\n+\s*\n+\s*(?=[^\s]+?)', file))+1
  error = False
  
  lines = open(text_file, 'r')
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

    # Print error
    if (a == 0 or a == 1 or (not answerSelected) or multipleAnswersSelected or questionText.text.startswith('*')):
      if(a == 0):
        print('No answer options were provided for question {}.'.format(i+1))
      if(a == 1):
        print('Only one answer option was provided for question {}.'.format(i+1))
      if(not answerSelected):
        print('No answer is selected for question {}.'.format(i+1))
      if(multipleAnswersSelected):
        print('Multiple answers are selected for question {}.'.format(i+1))
      if(questionText.text.startswith('*')):
        print("WARNING: Question {} begins with a '*' character.".format(i+1))
      print('\n Question {}: '.format(i+1) + questionText.text + '\n\n')
      error = True

  # Quit program
  if(error):
    print("Output file will not be produced. Fix input text and try again.")
    input("Hit 'Enter' to exit.")
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

  numQuestions = len(re.findall(r'[^\s]+?\s*\n+\s*\n+\s*(?=[^\s]+?)', file))+1
    
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




# Main Code

# Assign the input file to 'text_file'
text_file = glob.glob('convert *.txt')

# Check for errors
if len(text_file) > 1:
  print('ERROR, more than 1 convert file.')
  print('Below are the given convert files.')
  for i in text_file:
    print(i)
  input('ERROR, more than 1 convert file.')
  sys.exit()
elif len(text_file) == 0:
  print("ERROR. No file to convert. The program converts any '.txt' file in the")
  input("same directory which has a filename starting with 'convert '.")
  sys.exit()
else:
  text_file = text_file[0]
text_to_xml_error_check(text_file)

# Get the quiz name from the user
print("Note, file names cannot include any of the following characters:\n  \/:*?\"<>|")
QuizName = input("Enter the name of your quiz: ")

# Check if any character in QuizName is in \/:*?"<>|
c = ':'
nameIsValid = True
for char in QuizName:
  if char in "\/:*?\"<>|":
    nameIsValid = False
    c = char
while(not nameIsValid):
  print(f"'{c}' is not allowed in a file name.")
  QuizName = input("Enter a valid name for your quiz: ")
  nameIsValid = True
  for char in QuizName:
    if char in "\/:*?\"<>|":
      nameIsValid = False
      c = char
      
# Check if a zip file with the same name already exists
x = 'q'
if(os.path.exists(f'{QuizName}.zip')):
  print("Because a zip file with that name already exists, the new output file")
  print("will have the same name with the date and time appended to the end of")
  print("its title. Press 'Enter' to accept. If you wish to replace the prior")
  x = input("output file instead, type 'r' then hit 'Enter'.\n\n")

# Create zipped files
text_to_xml(text_file, 'res00001.dat', QuizName)
create_manifest()

# Zip the XML and manifest files into a folder with a proper name
if(x.lower() == 'r'):
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
if(os.path.exists(new_name)):
  print(f"The input file\n'{new_name}'\nalready has a converted file with the same name. Type 'r' then hit 'Enter'")
  print("if you wish to replace it. Otherwise hit 'Enter', and the input text")
  r = input("file will have its time and date appended to the end of its name.\n\n")
  if(r.lower() == 'r'):
    try:
      os.remove(new_name)
    except OSError:
      pass    
  else:
    time_now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    new_name = f'{new_name[:-4]}_{time_now}.txt'
try:
  shutil.copy(text_file, new_name)
  os.remove(text_file)
except:
  print("ERROR. Could not rename input text file because it is being")
  print("used somewhere else (likely in a terminal or in another instance")
  print("of this program). Instead another copy of the input text file")
  input("was made and renamed. Please delete original copy manually.")
