# Importing all the packages
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from tqdm import tqdm
from operator import add

# We start with all the parameters you would reasonably want to change, and define them here for clarity

# The number of settlements in the average wealth and Theil plots
number_of_xticks = 25

# The number of loops for the monte carlo and reconstruction loops
number_of_loops = 10

# The amount we assign for everyone who was not assessed due to poverty
amountPovertyAssessment = 2/12

# Flags for the run, turn them to True if you want certain plots
last_name_occupation = True
apprentice_as_master = False
if last_name_occupation:
    print("Last names as occupation is ON")
else:
    print("Last names as occupation is OFF")
if apprentice_as_master:
    print("Servant same sector employer is ON")
else:
    print("Servant same sector employer is OFF")

# Plot parameters
params = {
    "font.size": 12,
    "figure.figsize": (6.4, 4.8),
    "figure.subplot.left": 0.0,
    "figure.subplot.right": 1,
    "figure.subplot.bottom": 0,
    "figure.subplot.top": 1,
    "figure.subplot.wspace": 0,
    "figure.subplot.hspace": 0,
    "lines.markersize": 6,
    "lines.linewidth": 3.0,
    "figure.max_open_warning": 0,
    "mathtext.fontset": 'cm' 
}
plt.rcParams.update(params)

# Make it so we can use the correct fonts
from matplotlib import font_manager

# Insert where the fonts are stored here!
font_dir = [r'C:\Users\LeonK\AppData\Local\Microsoft\Windows']
for font in font_manager.findSystemFonts(font_dir):
    try:
        font_manager.fontManager.addfont(font)
    except:
        continue
   
plt.rcParams["font.family"] = "Linux Libertine Display O"
plt.clf()


# The settlement class contains the information of a settlement and a list of all its
# people (see class below). It also contains some functions to return information of the
# people within said settlement.
class Settlement:
    id = 0
    # I could create something to add the people to the Settlement
    def __init__(self, name, county, totalAssessments1381, people):
        self.name = name
        Settlement.id += 1
        self.id = Settlement.id
        self.county = county
        self.totalAssessments1381 = int(totalAssessments1381)
        self.people = people
        self.decreaseFactor = self.Factor(self.county,self.name)
        self.survivingAssessments = len(self.people)
        self.giniArray = np.array([])
        self.nArray = np.array([])
        self.weightsArray = np.array([])
        self.averageAdultInhabitants = 0
    
        # It is rare to happen, but sometimes the number of surviving assessments is greater
        # than the number of total assessments as given by the exchequer or the summa summarum,
        # due to counting errors etc. If so, we set the total equal to the surviving assessments.
        if self.survivingAssessments > self.totalAssessments1381:
            self.totalAssessments1381 = self.survivingAssessments
        
    # Determine the factor of loss between 1377 and 1381. The factor is the percentage decrease
    def Factor(self,county,name):
        # Here be the counties
        countyDictionary = {"Bedfordshire" : 26.9,"Berkshire" : 30.9,"Buckinghamshire":27.1,
                            "Cambridgeshire" : 11.1, "Cornwall" : 64.8, "Cumberland": 59.9,
                            "Derbyshire" : 32.7, "Devon" : 54.7, "Dorset" : 43, "Essex": 35.9,
                            "Gloucestershire" : 24.2, "Hampshire" : 33.8, "Herefordshire": 17.4,
                            "Hertfordshire": 33.4, "Huntingdonshire": 20.3, "Kent": 22.5,
                            "Lancashire" : 64.9, "Leicestershire": 30.9, "Lincolnshire":31.7,
                            "London": 12.5, "Middlesex": 11.6, "Norfolk":24.9,
                            "Northamptonshire":30.4, "Nottinghamshire": 33.6,
                            "Oxfordshire": 17.6, "Rutland":6.7, "Shropshire": 47.0,
                            "Somerset":51.7,"Staffordshire": 25.5,"Suffolk":23.8, "Surrey":34.7,
                            "Sussex":24.7, "Warwickshire": 19.5, "Westmorland": 47.8, "Worcestershire":17.1,
                            "Yorkshire":46.8, "Lincolnshire Lindsey":36.1, "Wiltshire":28.1}    
        # The largest cities
        cityDictionary = {"York": 44.6, "Salisbury":15.1, "Canterbury": 17.5, "Oxford":14.9, 
                          "Shrewsbury":22.3, "Boston": 44.4, "Worcester": 40.1, "Bath":47.9, "Lichfield": 23.4,
                          "Reading": 27.1, "Cirencester": 23.1, "Hadleigh": 23.1, "Chichester":12.7}

        try:
            return cityDictionary[name.strip()]
        except KeyError:
            return countyDictionary[county.strip()]
    
    def AverageAssessment(self):
        return np.average([person.assessment for person in self.people])
    
    def AssessmentsMarried(self, filterAssessment = 0):
        tempAssessments =  np.array([person.assessment for person in self.people
                         if person.married == True])
        if filterAssessment == 0:
            return tempAssessments
        else:
            return tempAssessments[tempAssessments<filterAssessment]
    
    # Gender should be M, F or U
    def AssessmentsUnmarried(self, gender, filterAssessment = 0):
        tempAssessments = np.array([person.assessment for person in self.people
                                    if (person.married == False and person.gender == gender)])
        if filterAssessment == 0:
            return tempAssessments
        else:
            return tempAssessments[tempAssessments<filterAssessment]
    


# The person class, this contains all the possible info of a person (at least, for the poll tax)
class Person:
    id = 0
    def __init__(self, firstName, lastName, assessment, gender, work, married, village, hundred, ward, county, employer, employee, servRightLoc):
        self.firstName = firstName
        self.lastName = lastName
        self.assessment = assessment
        self.gender = gender
        self.work = work
        self.married = married
        self.village = village
        self.hundred = hundred
        self.ward = ward
        Person.id += 1
        self.id = Person.id
        self.sector = SectorFromWork(self.work)
        self.county = county
        self.employer = employer
        self.employee = employee
        self.servRightLoc = servRightLoc
   
# Calculate the gini of a person
def Gini(x):
    rank = np.argsort(np.argsort(x))
    return 2*np.cov(rank, x, ddof=0)[1,0]/(np.sum(x))*len(x)/(len(x)-1)

# Calculate the Theil of a person, return 0 if there are none to calculate
def Theil(x, total):
    if len(x) == 0:
        return 0
    mean = np.mean(total)
    length = len(total)
    # delete all values of 0, these are 0 anyway
    x = x[x!=0]
    return np.sum(x/mean*np.log(x/mean))/length

def share_biggest(x):
    xNew = np.histogram(x*12,bins=np.arange(2,249, step = 2))[0]
    p_x = xNew/np.sum(xNew)
    return max(p_x)

def MaxPossibleEntropy(x):
    if x < 46:
        return -np.log(1/x)
    else:
        factor = divmod(x,46)[0]
        extra = divmod(x,46)[1]
        return -(46-extra)*factor/x*np.log(factor/x) - extra*(factor + 1)/x*np.log((factor + 1)/x)

def ModifiedGiniEntropy(x):
    xNew = np.histogram(x*12,bins=np.arange(2,249, step = 1))[0]
    p_x = xNew/np.sum(xNew)
    return 1 - np.sum(p_x**4)

def NormalisedShannonEntropy(x):
    number_under_4s = len(x[x<4.0001])
    xNew = np.histogram(x*12,bins=np.arange(2,49, step = 2))[0]
    p_x = xNew/np.sum(xNew)
    # return 1 - sum(p_x**4)
    
    p_x[p_x==0] = 1e-12 #since log(0) is not defined
    return -np.sum(p_x*np.log(p_x))/MaxPossibleEntropy(number_under_4s) #normalise it by the max obtainable entropy

# Determine the sector from someones work
def SectorFromWork(work):
    # Old backup file, the real one is imported from an .csv sheet
    workDictionary = {"": "Agriculture", "cult": "Agriculture", "labo" : "Labourer", "serv": "Servant",
                      "terr": "Agriculture", "s'": "Servant", "agri" : "Agriculture", "famu":"Servant",
                      "lab'": "Labourer", "tene": "Agriculture", "arti": "Artisan", "lib'": "Agriculture",
                      "t' t": "Agriculture", "***": "Other","caru": "Other", "carp": "Artisan","oper":"Labourer",
                      "text": "Artisan","fila":"Artisan","suto":"Artisan","tail":"Artisan","art'":"Artisan",
                      "bras":"Artisan","ciss":"Artisan","anci":"Servant","spyn":"Artisan","full":"Artisan",
                      "boch":"Artisan","merc":"Artisan","cota":"Agriculture","perc":"Agriculture","pisc":"Agriculture",
                      "webs":"Artisan","drap":"Artisan","fabe":"Artisan","carn":"Artisan","pist":"Artisan",
                      "nat'":"Agriculture","brac":"Artisan","shep":"Agriculture","cot'":"Other","nati":"Agriculture",
                      "cord":"Artisan","tayl":"Artisan","skyn":"Artisan","maso":"Artisan","fab'":"Artisan",
                      "fabr":"Artisan","ten'":"Agriculture","mole":"Artisan","fran":"Agriculture"}
    
    # If someone is a wife or a servant, look here (we need to delete the last two characters)
    if work[:1] == "s'":
        return "Servant"
    if work[-2:] == "_M" or work[-2:] == "_S":
        try:
            tempSector = dictSectors[work[:-2].strip().lower()]
        except:
            tempSector = "Not identified"
            notknown.append(work[:-2])
        if tempSector == "":
            tempSector = "Not identified"
        if work[-2:] == "_M":
            return str(tempSector) + "_M"
        return str(tempSector)
    
    # If someone is not a servant or a wife
    try:
        tempSector = dictSectors[work.strip().lower()]
    except:
        tempSector = "Not identified"
        notknown.append(work)
    if tempSector == "":
        tempSector = "Not identified"

    return tempSector

# Determine someones gender from their name
def GenderFromName(name,x):
    # The dictionary with (nearly) all the unique names
    nameDictionary = {"Johannes": "M", "Alicia" : "F", "Willelmus": "M", "Johanna" : "F",
                  "Johanne": "M", "Agn'": "F", "Thomas": "F", "Ricardus":"M", "Robertus": "M",
                  "Willelmo": "M", "Isabella": "F","Matilda": "F", "Johannes ": "M",
                  "Henricus": "M", "Marg'": "F", "Thoma":"M", "Roberto": "M", "Margeria": "F",
                  "Rogerus":"M", "Emma":"F","Ricardo":"M","Margareta":"F","Alicia ":"F","Mattill'":"F",
                  "Willemus ":"M","Walterus":"M","Juliana":"F","Nicholaus":"M","Adam":"M","Elena": "F",
                  "Editha":"F","Thomas ":"M","Henrico":"M","Katerina":"F","Johanna ":"F","Amicia":"F",
                  "Hugo":"M","Is'":"F","Cecilia":"F","Ricardus ":"M","Cristina":"F","Johanne ":"M",
                  "Rogero":"M","Sibilla":"F","Galfridus":"M","Agneta":"F","Jul'":"F","Waltero":"M",
                  "Christina":"F","Robertus":"M","Simon":"M","Stephanus":"M","Petrus":"M","Hugone": "M",
                  "Radulphus":"M","Agn' ":"F","Nicholao":"M","Felicia":"F","Lucia":"F","  Johannes":"M",
                  "Elizabetha":"F","Beatrix":"F","Margr'":"F","Isabella ":"F","Christiana":"F",
                  "Thoma ":"M", "Philippus":"M","Walterus ":"M", "Rosa":"F","Petronilla":"F","Margeria ":"F",
                  "Dionisia":"F","Isolda":"F","Henricus ":"M","Matilda ":"F","Leticia":"F","Ricardo ":'M',
                  "Sarra":"F","Avicia":"F","Simone":"M","Editha ":"F","Beatice":"F","Agnes'":"F",
                  "Rogerus ":"M","Mariota": "F","Juliana ":"F","Christiana":"F","Thoma ": "M","Philippus":"M",
                  "Walterus ":"M","Rosa":"F","Petronilla":"F","Margeria ":"F", "Elena": "F", "Andrea": "M",
                  "Jacobo" : "M", "Galfrido": "M", "Radulpho" : "M", "Deonisio": "M", "Mat'": "F", 
                  "Petro" : "M", "Stephano" : "M", "...": "U", "Alexandre": "M", "Edwardo": "M", "Edo" : "M",
                  "Reginaldo":"M","Laurencio":"M", "Philippo": "M", "Florencia": "F", "Edytha": "F",
                  "Davido": "M", "David": "M", "Agatha":"F","Mag'":"F", "Wilelmo":"M", "Dionis'": "M",
                  "Gilberto":"M","Emmota": "F", "Morc'": "M", "Cicilla":"F","Mabella":"F","Ibota":"F",
                  "Cecylia":"F","Johas":"M","Fulcone": "M", "Moricio":"M", "Tybbe": "M","Magota":"F",
                  "Robard":"M","Sibely":"U","Michaele":"M","Richardo":"M","Maria":"F","Ingeram":"M",
                  "Clemente":"M","Amisia":"F","Egidio":"M","nn":"U","Rybon'":"M","Edmundo":"M",
                  "Mariona":"F", "Guydone":"M","filio":"M","Margereta":"M","Nichola":"F","Grigorio":"M",
                  "Almarico":"M", "Helawysia":"M", "Longeman'":"M","Warino":"M","Isota":"F",
                  "Jec'":"M","Johayn":"M","Harveo":"M","Gregorio":"M","Kenne":"M","Wat'":"M",
                  "Anabila":"F","Ammer'":"M","Domine":"M","Dionisio":"M", "nnman":"M","nnwoman":"F","nn":"U",
                  "Jacobus":"M","Alanus":"M","Alexander":"M","Matill'":"F","Gilbertus":"M","Agnes":"F","Mar'":"F",
                  "Johanens":"M","Fulco":"M","Cecillia":"F","Mabilla":"F","Andreas":"M","Angn'":"F","Jonetta":"F",
                  "Dulcia":"F","Cicilia":"F","Emota":"F","Edmundus":"M","Beatrice":"F","Eva":"F","Christiania":"F",
                  "Reginaldus":"M","Laurencius":"F","Lambertus":"F","Constancia":"F","Ivetta":"F","Matheus":"M",
                  "Custancia":"F","Benedicta":"F"}
    try:
        tempGender = nameDictionary[name.strip()]
    except:
        # If the name is not there, use the gender as indicated by the CAMPOP people
        tempGender = x[12]
    return tempGender

# These settlements have no scaling and should be ignored
def VillageNoScaling(name):
    list_thing = ['Little Soudley','Moston','Kingston Deverill','Stanton upon Hine Heath',
     'Timberth','Frome Biller','Frampton Mansell','Stockton','Kenstone','Osbaston',
     'Woodcote','Kintbury','Adney','Howle','Keythorpe','Newbold','Avington','Hopton and Espley',
     'Chickerell','Brocksby','Bromlow','Great Stretton','Hamstead Marshall','Kingston Maurward',
     'Stean Bridge and Bisley [pcl]','Stinsford','Priestweston','Binweston','Ingarsby',
     'Little Yeldham','Tipton','Wotherton','Upwey','Pusey','Wrickton and Walkerslow',
     'Billingsley','Wollaston with parcels','Great Saling','Dodlington','Lyford',
     'Rolleston','Frome Whitfield','[Winnington with parcels]','Pulston with Forston',
     "King's Norton",'Middleton','Shangton','Westley','Great Saxham','Meysey Hampton',
     'Edgmond','Hargrave','(Liston)','Charney Bassett','Goodby Marwood','Lamarsh',
     'Frilford','Donnington','Grafton','Wistow','Burrough on the Hill','Marsh Benham',
     'Ashton under Hill','Broadmayne','Hinton on the Green','Galy','Pebmarsh','Stow Bardolph with Wimbotsham',
     'Beckford',"Salisbury","Shrewsbury", "Kessingland"]
        #Salisbury and Shrewsbury do have scaling, but they are much too fragmented to be used, so I just put them here.
    if name in list_thing:
        return True
    return False

# This reconstructs the missing assessments from 1381
def ReconstructLostAssessments(settlement):

    if settlement.totalAssessments1381 > settlement.survivingAssessments:
        sortedAssessments = np.sort([person.assessment for person in settlement.people])
        # print("A: " + str(sortedAssessments))
        x = np.linspace(0,1,num = len(sortedAssessments))
        reconstructedAssessments = []
        # For every missing assessment, pick a random number between 0 and 1
        randomNumbers = np.random.rand(settlement.totalAssessments1381 - len(sortedAssessments))
        # Then, sample the missing assessments using inverse transform sampling
        for i in randomNumbers:
            reconstructedAssessments.append(sortedAssessments[np.where(x == x[x<i][-1])][0])
        newAssessments = np.append(sortedAssessments,reconstructedAssessments)
        return newAssessments
    else:
        return [person.assessment for person in settlement.people]

# Here, all the people are created
def CreatePerson(x):
    listPeople = []
    actual_assessments = []
    previousUnreadable = False
    
    # Loop over the full data
    for i in range(len(x)-2):
        # x is the full string of an entry in the spreadsheet, corresponding to a person
        # Split the string into bits using the ; character
        temparray = x[i + 1].split(';')
        # If an entry does not correspond to 1381, skip it
        if temparray[0] != str(1381):
            continue
        
        # If the data contains an artifact in the assessments or is otherwise unreadable, skip it and mark
        # the previously read person as unreadable.
        if (temparray[8] == '**' or temparray[8] == 'â€¦' or temparray[8] == '***' or
            temparray[8] == '..' or temparray[7] == '.' or temparray[8] == '*' or
            temparray[7] == 'â€¦' or temparray[8] == 'Â·Â·Â·' or temparray[8] == 'â€¦.' or
            temparray[8] == 'Â·Â·' or temparray[7] == 'Â·Â·Â·' or temparray[8] == '…' or
            temparray[8] == '•••' or temparray[8] == '•• ' or temparray[7] == '…' or
            temparray[7] == '*' or temparray[8] == '** ' or temparray[8] == '**/' or
            temparray[8] == '...' or temparray[8] == '.' or temparray[8] == 'sic' or
            temparray[8] == '···' or temparray[8] == '….' or temparray[8] == '··' or 
            temparray[7] == '···' or temparray[7] == ' ' or temparray[7] == 'sic'):
            previousUnreadable = True
            continue
        
        # All the info is now stored in specific parts of the temparray array, such as county on index 2
        county = temparray[2]
        work = temparray[13].strip()[:4]
        pence = temparray[8]
        
        if pence == '': pence = 0
        shillings = temparray[7]
        if shillings == '': shillings = 0
        # recalculate the total assessment in terms of shillings
        try:
            assessment = float(shillings) + float(pence)/12
        except:
            continue
        name = temparray[9]
        lastname = temparray[10]
        gender = GenderFromName(name, temparray)
        if gender == '':
            gender = 'U'
        married = False
        
        servRightLoc = False
        if temparray[15] == "y":
            servRightLoc = True
            
        
        # Here we can take the surname as indicative of profession if no profession is named
        if last_name_occupation:
            if work == "":
                tempwork = SectorFromWork(lastname.strip()[:4])
                if tempwork != "Not identified":
                    work = lastname.strip()[:4]

        ward = None
        hundred = temparray[3]
        if temparray[17] != '':
            village = temparray[17].strip()
            ward = temparray[5]
        elif temparray[5] != '':
            village = temparray[5].strip()
        elif temparray[4] != '':
            village = temparray[4].strip()
        else:
            village = ''
            continue
                
        # Here, we deal with wives
        if (lastname[:2] == "ux"):
            # If someone is a wife and her husband is unreadable, we again skip
            if previousUnreadable:
                continue
            # There are some instances where two "ux" follow each other,
            # This is due to spelling variations being entered twice as different
            # People, ignore these.
            elif listPeople[-1].gender == "Married F":
                continue
            
            else:
                # Set the gender of someone to reflect their marital state
                gender = "Married F"
                listPeople[-1].gender = "Married M"
                married = True
                listPeople[-1].married = True
                # If she has no separate assessment, we use half of her husband
                if assessment == 0:
                    listPeople[-1].assessment = listPeople[-1].assessment/2
                    assessment = listPeople[-1].assessment
                    # actual_assessments[-1] = actual_assessments[-1]/2
                    # actual_assessments.append(actual_assessments[-1])
                else:
                    percentage_assessment_wife.append(listPeople[-1].assessment/assessment)
                    percentage_assessment_wife_villages.append(village)
                if work == "":
                    # If she has no explicit occupation, use that of her husband
                    work = str(listPeople[-1].work.strip()) + "_M"
        
        # This is someone who is a son or daughter
        elif (lastname[:3] == "fil" or lastname[:3] == "Fil"):
            if previousUnreadable:
                continue
            # Show that they are a child in their gender
            gender = "Child " + gender
            # Use one third of their parents wealth as their wealth
            if assessment == 0:
                listPeople[-1].assessment = listPeople[-1].assessment*2/3
                listPeople[-2].assessment = listPeople[-2].assessment*2/3
                assessment = listPeople[-1].assessment
            # Children with no work are assumed to help their parents with their work, functionally as a servant
            
            if work == "":
                tempwork = listPeople[-1].work
                if tempwork[-2:] == "_M":
                    tempwork = tempwork[:-2]
                if tempwork[-2:] == "_S":
                    # print(listPeople[-1].work)
                    work = tempwork
                elif tempwork != "":
                    work = tempwork + "_S"
                
        
        # If someone has no assessment, we skip them
        elif assessment == 0:
            previousUnreadable = True
            continue
        
        employer = False
        employee = False    
        
        # Make an employer noted as one
        temp_sect = SectorFromWork(work)
        # Set all servants and labourers as employees
        if temp_sect == "Servant" or temp_sect == "Labourer":
            employee = True
            if servRightLoc == True:
                if previousUnreadable == False and temp_sect == "Servant":
                    if listPeople[-1].sector[-2:] == "_M":
                        if listPeople[-2].sector != "Servant":
                            # If an employer is married, both people in the marriage are employers
                            listPeople[-1].employer = True
                            listPeople[-2].employer = True
                    # If an employer has children they might be mentioned before
                    elif listPeople[-1].gender[:5] == "Child":
                        for teller in [1,2,3,4,5]: #check at most 5 people back
                            if listPeople[-1-teller].gender[:5] != "Child":
                                if listPeople[-1-teller].sector[-2:] == "_M":
                                    if listPeople[-2-teller].sector != "Servant":
                                        # If an employer is married, both people in the marriage are employers
                                        listPeople[-1-teller].employer = True
                                        listPeople[-2-teller].employer = True
                                        break
                                elif listPeople[-1-teller].sector != "Servant":
                                    listPeople[-1-teller].employer = True
                                    break
                    elif listPeople[-1].sector != "Servant":
                        listPeople[-1].employer = True
                
        

        if apprentice_as_master:
            temp_sect = SectorFromWork(work)
            if temp_sect == "Servant":
                if servRightLoc == True:
                    if previousUnreadable == False:
                        tempwork = listPeople[-1].work
                        if tempwork[-2:] == "_M":
                            tempwork = tempwork[:-2]
                        if tempwork[-2:] == "_S":
                            # print(listPeople[-1].work)
                            work = tempwork
                        elif tempwork != "":
                            work = tempwork + "_S"

         # Do the rescaling for Oxford and York
        if village == "Oxford":
             assessment = RescaleOxford(ward, assessment)
             
        elif village == "York":
             assessment = RescaleYork(ward, assessment)
         
        if assessment == 0:
             continue

        # create the person and append it to the list
        listPeople.append(Person(name, lastname, assessment, gender, work, married, village, hundred, ward,county,employer,employee,servRightLoc))
        previousUnreadable = False
        
        # The actual_assessments stores the unscaled assessments and is used for 
        # the analysis of the assessments as directly assigned (i.e. without halving
        # the assessments for married couples)
        actual_assessments.append(float(shillings) + float(pence)/12)
        
    return listPeople, actual_assessments
 
    
# Rescale York:
def RescaleYork(ward, assessment):
    if ward == "St Crux (Pavement)":
        return assessment
    elif ward == "St Helens (Stonegate)":
        return assessment*0.75
    elif ward == "St Michael (Spurruergate)":
        return assessment*0.9
    elif ward == "All Saints (North Street)":
        return assessment*0.83
    elif ward == "All Saints (Pavement)":
        return assessment*0.78
    elif ward == "St Martin (Coney Street)":
        return assessment*1.11
    elif ward == "St John (Ouse Bridge End)":
        return assessment
    elif ward == "St Sampson (Girdlergate)":
        return assessment
    elif ward == "Holy Trinity (Micklegate)":
        return assessment
    elif ward == "St Mary (Castlegate)":
        return assessment*0.77
    elif ward == "St Mary (Bishophill Senior)":
       return assessment*0.96
    elif ward == "[St Olave (Marygate and St Giles (Gallygate)]":
        return assessment*0.75
    elif ward == "St Michael-le-Belfrey":
        return assessment
    elif ward == "St. Martin (Micklegate) and St Gregory (Micklegate)":
        return assessment
    elif ward == "Holy Trinity (King's Court)":
        return assessment
    elif ward == "St John-del-Pike":
        return assessment*0.51
    elif ward == "St Saviour (St Saviourgate)":
        return assessment*0.83
    elif ward == "St Mary and St argaret (Walmgate)":
        return assessment*0.43
    elif ward == "St Andrew (Andrewgate)":
        return assessment*0.52
    elif ward == "St Wilfrid (Blake Street)":
        return assessment*0.75
    elif ward == "Holy Trinity (Goodramgate)":
        return assessment
    else:
        return 0

def RescaleOxford(ward, assessment):
    if ward == "North East Ward":
        return assessment
    elif ward == "South East Ward":
        return assessment/9.4*7.4
    elif ward == "South West Ward":
        return assessment/8.5*7.4
    elif ward == "Reassessment":
        return assessment/6.4*7.4
    elif ward == "St Thome":
        return assessment/12.5*7.4
    elif ward == "St Mary Magdalen":
        return assessment/9.3*7.4
    elif ward == "St Giles":
        return assessment/10*7.4
    else:
        return 0
    
    
def FilterSettlements(listPeople, UniqueCountySettlementList):
    
    # To keep track of why settlments are rejected
    rejectedGini = 0
    notinlist = 0
    rejectedOther = 0
    
    # What this function will be returning
    filteredSettlementList = []
    allPeopleAfterFilterArr = np.array([])
    rejectedGiniEntropyArray = np.array([0,0,0])
    
    numberOfAssessments = 0
        
    # Perform the first filters, by looping over all unique combinations of counties
    # and settlements.
    for countySettlement in tqdm(UniqueCountySettlementList):
        
        county, settlement = countySettlement.split(';')
        workingSetPeople = []
        
        # Uncomment and substitute below if you wish to only look at a specific county
# =============================================================================
#         if county not in ["Somerset"]:
#             continue
# =============================================================================
        
        for person in listPeople:
            if person.county == county and person.village == settlement:
                workingSetPeople.append(person)
        
        # Check if the total size is known
        if (county + settlement) in knownCountySettlementList:
            
            # The number of known inhabitants
            numberOfKnownInhabitants = array_size_vills[knownCountySettlementList.index(county + settlement),2]
            
            # If the number contains a '+', that means we don't know the total!
            if '+' in numberOfKnownInhabitants:
                rejectedOther += 1
                continue
            
            # Check if the settlement contains more than 10 people
            elif int(numberOfKnownInhabitants) < 10:
                rejectedOther += 1
                continue
            
            # Check if more than 35% has survived
            elif len(workingSetPeople)/int(numberOfKnownInhabitants) < 0.35:
                rejectedOther += 1
                continue
         
        # Print the settlement and county if they are not known
        else:
            print("Vill not in vill list:" + settlement +  ", county: " + county)
            notinlist += 1
            continue
        
        # An array of the assessments in the settlement
        assessmentsWorkingSet = np.array([person.assessment for person in workingSetPeople])
        
        # Calculate the average assessment for the settlement, and if it is not between 0.9 and 1.1, we dismiss the settlement
        if np.mean(assessmentsWorkingSet) > 1.1 or np.mean(assessmentsWorkingSet) < 0.9:
            if settlement != "York" and settlement != "Oxford":
                rejectedOther += 1
                continue

        # Calculate the modified Gini entropy value and reject if below a threshold
        if ModifiedGiniEntropy(assessmentsWorkingSet) < 0.9:
            rejectedGini = rejectedGini + 1
            rejectedGiniEntropyArray = np.vstack((rejectedGiniEntropyArray, 
                                                  np.array([Gini(assessmentsWorkingSet),ModifiedGiniEntropy(assessmentsWorkingSet), NormalisedShannonEntropy(assessmentsWorkingSet)])))
            continue
          
        # We want to filter out any settlements that only note the head of the household,
        # which we check by seeing if there are any married women present.
        marriedWomanPresent = False
        for person in workingSetPeople:
            if person.gender == 'Married F':
                marriedWomanPresent = True
                continue
        
        if not marriedWomanPresent:
            rejectedOther += 1
            continue

        giniEntropyList.append(ModifiedGiniEntropy(assessmentsWorkingSet))
        Shannon_prelim.append(NormalisedShannonEntropy(assessmentsWorkingSet))
        Gini_prelim.append(Gini(assessmentsWorkingSet))
        
        workingSettlement = Settlement(settlement,
                                       county,numberOfKnownInhabitants,workingSetPeople)
        
        numberOfAssessments += len(workingSetPeople)
        
    # =============================================================================
    #     settlement_size.append(len(temp_total))
    #     share_biggest_arr.append(share_biggest(temp_total))
    #     frac_below.append(len(temp_total[temp_total<1])/len(temp_total))
    # =============================================================================
        
        filteredSettlementList.append(workingSettlement)
        allPeopleAfterFilterArr = np.append(allPeopleAfterFilterArr, workingSetPeople)
    
    print("Overall, " + str(len(filteredSettlementList)) + " villages are accepted")
    print(str(rejectedGini) + " villages are rejected due to entropy")
    print(str(notinlist) + " villages are rejected due to not being in the settlement list")
    print(str(rejectedOther) + " villages are rejected due to other reasons")
    print(str(numberOfAssessments) + " assessments have survived.")
        
    return filteredSettlementList, allPeopleAfterFilterArr, rejectedGiniEntropyArray

# Here, set the location to be the files we wish to import!
fileloc1 = r"C:\Users\LeonK\Documents\Studie\MA Renaissance\Thesis\poll_tax_1381\campop_1.csv"
fileloc2 = r"C:\Users\LeonK\Documents\Studie\MA Renaissance\Thesis\poll_tax_1381\campop_2.csv"
fileloc3 = r"C:\Users\LeonK\Documents\Studie\MA Renaissance\Thesis\poll_tax_1381\campop_3.csv"
fileloc4 = r"C:\Users\LeonK\Documents\Studie\MA Renaissance\Thesis\poll_tax_1381\addendum_kamermans.csv"
# This is the files where I defined the different occupations beloning to certain sectors
fileSectors = r"C:\Users\LeonK\Documents\Studie\MA Renaissance\Thesis\poll_tax_1381\sectorsCSV.csv"
fileSizeVills = r"C:\Users\LeonK\Documents\Studie\MA Renaissance\Thesis\poll_tax_1381\List_size_vills.csv"

file1 = np.array(open(fileloc1,'r').read().split('\n'))
file2 = np.array(open(fileloc2,'r').read().split('\n'))
file3 = np.array(open(fileloc3,'r').read().split('\n'))
file4 = np.array(open(fileloc4,'r').read().split('\n'))
fileSectors = np.array(open(fileSectors,'r').read().split('\n'))
dictSectors = {}
for i in fileSectors[1:-1]:
    j = i.split(";")
    dictSectors.update({j[0]:j[1]})
    
# This list will contain all unidentified occupations
notknown = []

file_size_vills = np.array(open(fileSizeVills).read().split('\n'))
array_size_vills = np.array([0,0,0])

for i in range(len(file_size_vills)-2):
    # x is the full string of an entry in the spreadsheet, corresponding to a person
    # Split the string into bits using the ; character
    temparray = file_size_vills[i + 1].split(';')
    array_size_vills = np.vstack((array_size_vills,temparray))
array_size_vills=array_size_vills[1:]

emptyarray = np.zeros(len(file1[0].split(';')))

# bigfile is every file combined
bigfile = np.append(file1,file2)
bigfile = np.append(bigfile,file3)
bigfile = np.append(bigfile,file4)

# bigfile = file4

percentage_assessment_wife = []
percentage_assessment_wife_villages = []

print("I still need to put the 'right placement' for all servants in big settlements not in my addendum...")
# Here, we create all the people
listPeople, actual_assessments = CreatePerson(bigfile)
actual_assessments2 = []

CountySettlementList = []

# Loop over everyone
for person in listPeople:

    CountySettlementList.append(str(person.county) + ";" + str(person.village))


UniqueCountySettlementList = set(CountySettlementList)


print("First Filter of Settlements:")

knownCountySettlementList = list(map(add,array_size_vills[:,0].tolist(), array_size_vills[:,1].tolist()))

Shannon_prelim = []
Gini_prelim = []
giniEntropyList = []


# Perform the first filters, by looping over all unique combinations of counties
# and settlements.
filteredSettlementList, allPeopleAfterFilterArr, rejectedGiniEntropyArray = FilterSettlements(
    listPeople, UniqueCountySettlementList)

percentage_assessment_wife_new = []
for i in range(len(percentage_assessment_wife)):
    if percentage_assessment_wife_villages[i] in filteredSettlementList:
        percentage_assessment_wife_new.append(percentage_assessment_wife[i])

plt.hist(percentage_assessment_wife_new, bins = [0,0.99,1.01,2,20])
plt.show()


# THE NORMALISATION OF THE FIRST PLOT IS NOW HARD-CODED IN, THIS SHOULD BE IMPROVED
fig = plt.figure(figsize = (10,4))

gs = fig.add_gridspec(1,3, wspace=0, width_ratios = [8/26,10/26,8/26])
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])

listie = [ax1,ax2,ax3]

plt.rc('axes', axisbelow=True)
plt.rcParams.update({'font.size': 16})
# plt.rcParams.update({"figure.figsize": (10, 4.8)})
# plt.figure(constrained_layout="true")


giniArrayAll = np.append(Gini_prelim, rejectedGiniEntropyArray[:,0])
modifiedGiniEntropyArrayAll = np.append(np.array(giniEntropyList), rejectedGiniEntropyArray[:,1])
shannonEntropyArrayAll = np.append(np.array(Shannon_prelim), rejectedGiniEntropyArray[:,2])

listie[1].vlines(0.9,0,0.6, 'r', '--', zorder = 0)
h2, xedges2, yedges2, im2 = listie[1].hist2d(modifiedGiniEntropyArrayAll,giniArrayAll,range = [[0.001,1],[0,0.6]], bins = 50, cmap = 'viridis_r', cmin = 0.1, zorder = 1)
listie[1].set_xlabel(r'Modified Gini entropy $\tilde{G}$')
listie[1].set_yticks([0,0.1,0.2,0.3,0.4,0.5,0.6],[])
listie[1].set_xticks([0.2,0.4,0.6,0.8,1],[0.2,0.4,0.6,0.8,1])


h, xedges, yedges, im = listie[0].hist2d(shannonEntropyArrayAll,giniArrayAll,range = [[0.001,0.8],[0,0.6]], bins = 50, cmap = 'viridis_r', cmin = 0.1, vmax = np.max(h2[h2>0]))
listie[0].set_ylabel(r'Gini Index $G$')
listie[0].set_xlabel(r'Normalised Shannon Entropy $\bar{H}$')
listie[0].set_xticks([0.0,0.2,0.4,0.6,0.8],[0.0,0.2,0.4,0.6,0.8])
# plt.subplot(1,2,2)

h3, xedges, yedges, im3 = listie[2].hist2d(Shannon_prelim,Gini_prelim,range = [[0.001,0.8],[0,0.6]], bins = 50, cmap = 'viridis_r', cmin = 0.1, vmax = np.max(h2[h2>0]))
listie[2].set_xlabel(r'$\bar{H}$ for sett. with $\tilde{G} > 0.9$')
listie[2].set_xticks([0.2,0.4,0.6,0.8],[0.2,0.4,0.6,0.8])
listie[2].set_yticks([0,0.1,0.2,0.3,0.4,0.5,0.6],[])
# plt.subplot(1,2,2)

cbar = fig.colorbar(im, ax=listie, location="right", pad=0.02)

for ax in listie:
    ax.grid(True, which="major", axis="y", zorder=-1)
    ax.grid(True, which="minor", axis="y", linestyle="--", alpha=0.3)
    ax.grid(True, which="major", axis="x", zorder=-1)
    ax.grid(True, which="minor", axis="x", linestyle="--", alpha=0.3)


plt.savefig('GiniVsEentropy.pdf', bbox_inches = "tight")
plt.show()


assessmentsAfterFilter = np.array([people.assessment for people in allPeopleAfterFilterArr])

totalDenarii = np.round(assessmentsAfterFilter*12)
    
plt.rc('axes', axisbelow=True)
plt.rcParams.update({'font.size': 16})
plt.rcParams.update({"figure.figsize": (10, 4.8)})
plt.figure(constrained_layout="true")
plt.hist(totalDenarii,bins=np.linspace(1,240,num=240), edgecolor='navy')
plt.xlim(0.5,72)
plt.xticks([0.5,4.5,6.5,8.5,12.5,16.5,18.5,20.5,24.5,30.5,36.5,40.5,42.5,48.5,54.5,60.5,72.5],[0,"4d","6d","8d","1s","1s4d","1s6d","1s8d","2s","2s6d","3s","3s4d","3s6d","4s","4s6d","5s","6s"],rotation = 60)
plt.yscale('log')
plt.grid(which = "major", axis="y", zorder = -1)
plt.grid(which = "minor", axis = "y", linestyle = "--", alpha = 0.3)
plt.xlabel("Assessment")
plt.ylabel("N")
plt.tight_layout()
plt.savefig("totaldistrshillings.pdf")
plt.show()

assessments = Counter(totalDenarii).keys()
waardes = Counter(totalDenarii).values()
waardes, assessments = zip(*sorted(zip(waardes,assessments)))

print("Five most Popular assessments:")
print(np.array(assessments[-5:]))
print(np.array(waardes[-5:])/len(totalDenarii))

genderAfterFilter = np.array([people.gender for people in allPeopleAfterFilterArr])
uniqueGenders = Counter(genderAfterFilter).keys()
uniqueGendersValues = Counter(genderAfterFilter).values()
uniqueGendersValues, uniqueGenders = zip(*sorted(zip(uniqueGendersValues,uniqueGenders)))

print(uniqueGenders)
print(uniqueGendersValues)

orderOfInhabitants = []
# Determine the correct order for the largest cities, such that they are in order of inhabitants for the plots:
for settlement in filteredSettlementList:
    orderOfInhabitants.append(int(int(settlement.totalAssessments1381)/(1-settlement.decreaseFactor/100)))

# Create the indices of the correct order
inds = np.array(orderOfInhabitants).argsort()
reconstructed_inhabitants = np.array(orderOfInhabitants)[inds]
# Reorder them 
reorderedSettlementList = np.array(filteredSettlementList)[inds]


# # Here, we have all the empty lists that will be filled in our analysis (there are a lot...)

list_top_one_percent = []
list_top_ten_percent = []
list_top_fifty_percent = []
list_bottom_fifty_percent = []

n_list_top_one_percent = []
n_list_top_ten_percent = []
# theil_list_unscaled = []
# n_list_unscaled = []
theilListMarried = []
theilListUnmarriedMen = []
theilListUnmarriedWomen = []
theilListTotal = []

averageListMarried = []
averageListUnmarriedWomen = []
averageListUnmarriedMen = []

averageListMarriedFiltered = []
averageListUnmarriedWomenFiltered = []
averageListUnmarriedMenFiltered = []

totalListMarriedRural = []
totalListUnmarriedMenRural = []
totalListUnmarriedWomenRural = []

numberInhabitants_10 = 0
numberInhabitants_175 = 0
numberInhabitants_25 = 0

weightArray = np.array([])
weightArrayOnePercent = np.array([])

wealthEmployersArray = np.array([])
wealthEmployeesArray = np.array([])
wealthNeitherEmployerEmployeeArray = np.array([])

wealthFemaleEmployeesArray = np.array([])
wealthMaleEmployeesArray = np.array([])

# underhundred_reconstructed_total = 0

# # This the logarithmic binning that will be used in our plots
logbins1 = np.linspace(10,50,num = 40)
logbins2 = np.linspace(np.log10(50),np.log10(10000),num = 300)
logbins = np.append(np.log10(logbins1),logbins2[1:])-0.01
middle_bins = logbins[:-1] + (logbins[:-1]-logbins[1:])/2

shannon_entropy = []

# We loop over every settlement. The tqdm allows for a progress bar to show up
for settlement in tqdm(reorderedSettlementList):
    
    # An array of the assessments in the settlement
    assessmentsWorkingSet = np.array([person.assessment for person in settlement.people])

    # villages3 contains the names of all the settlements we actually use and aren't skipped for some reason
    shannon_entropy.append(NormalisedShannonEntropy(assessmentsWorkingSet))


    if settlement in reorderedSettlementList[-number_of_xticks:]:

        employersInSettlement = sum(np.array([person.employer for person in settlement.people]))
        employeesInSettlement = sum(np.array([person.employee for person in settlement.people]))
        
        if employersInSettlement > 4 and employeesInSettlement > 4:
            
            wealthEmployers = np.mean([person.assessment for person in settlement.people if person.employer == True])
            wealthEmployees = np.mean([person.assessment for person in settlement.people if person.employee == True])
            wealthNeitherEmployerEmployee = np.mean([person.assessment for person in settlement.people if (person.employee == False and person.employer == False)])
        
            wealthEmployersArray = np.append(wealthEmployersArray, wealthEmployers)
            wealthEmployeesArray = np.append(wealthEmployeesArray, wealthEmployees)
            wealthNeitherEmployerEmployeeArray = np.append(wealthNeitherEmployerEmployeeArray, wealthNeitherEmployerEmployee)

        femaleEmployeesInSettlement = sum(np.array([person.employee for person in settlement.people if person.gender[-1] == "F"]))
        maleEmployeesInSettlement = sum(np.array([person.employee for person in settlement.people if person.gender[-1] == "M"]))

        if femaleEmployeesInSettlement > 2 and maleEmployeesInSettlement > 2:
            
            wealthFemaleEmployeesArray = np.append(wealthFemaleEmployeesArray, np.mean([person.assessment for person in settlement.people if (person.employee == True and person.gender[-1] == "F")]))
            wealthMaleEmployeesArray = np.append(wealthMaleEmployeesArray, np.mean([person.assessment for person in settlement.people if (person.employee == True and person.gender[-1] == "M")]))



    if settlement in reorderedSettlementList[-number_of_xticks:]:
        theil_unmarried_women = Theil(np.array([person.assessment for person in settlement.people if (person.gender == "F" or person.gender == "Child F") and person.assessment < 2.01]), assessmentsWorkingSet[assessmentsWorkingSet<2.01])
        theil_unmarried_men = Theil(np.array([person.assessment for person in settlement.people if (person.gender == "M" or person.gender == "Child M") and person.assessment < 2.01]), assessmentsWorkingSet[assessmentsWorkingSet<2.01])
        theil_married = Theil(np.array([person.assessment for person in settlement.people if (person.gender == "Married F" or person.gender == "Married M") and person.assessment < 2.01]), assessmentsWorkingSet[assessmentsWorkingSet<2.01])
        theil_total = Theil(assessmentsWorkingSet[assessmentsWorkingSet<2.01], assessmentsWorkingSet[assessmentsWorkingSet<2.01])
        theilListTotal.append(theil_total)
        theilListMarried.append(theil_married)
        theilListUnmarriedWomen.append(theil_unmarried_women)
        theilListUnmarriedMen.append(theil_unmarried_men)
        
        averageListUnmarriedWomen.append(np.average([person.assessment for person in settlement.people if (person.gender == "F" or person.gender == "Child F")]))
        averageListUnmarriedMen.append(np.average([person.assessment for person in settlement.people if (person.gender == "M" or person.gender == "Child M")]))
        averageListMarried.append(np.average([person.assessment for person in settlement.people if (person.gender == "Married F" or person.gender == "Married M")]))
    
        averageListUnmarriedWomenFiltered.append(np.average([person.assessment for person in settlement.people if (person.gender == "F" or person.gender == "Child F") and person.assessment < 2.01]))
        averageListUnmarriedMenFiltered.append(np.average([person.assessment for person in settlement.people if (person.gender == "M" or person.gender == "Child M") and person.assessment < 2.01]))
        averageListMarriedFiltered.append(np.average([person.assessment for person in settlement.people if (person.gender == "Married F" or person.gender == "Married M") and person.assessment < 2.01]))
    
    assessmentsWorkingSet = np.array([person.assessment for person in settlement.people])
    # Calculate the number of inhabitants in 1377 using different facors of 10, 17.5 and 25 percent
    inhabitants1377_25 = int(settlement.totalAssessments1381/(1-settlement.decreaseFactor/100)/(1-0.25))
    inhabitants1377_10 = int(settlement.totalAssessments1381/(1-settlement.decreaseFactor/100)/(1-0.1))
    inhabitants1377_17dot5 = int(settlement.totalAssessments1381/(1-settlement.decreaseFactor/100)/(1-0.175))
    
    settlement.averageAdultInhabitants = inhabitants1377_17dot5
    
    if settlement.averageAdultInhabitants < 100:
        totalListUnmarriedWomenRural += [person.assessment for person in settlement.people if (person.gender == "F" or person.gender == "Child F")]
        totalListUnmarriedMenRural += [person.assessment for person in settlement.people if (person.gender == "M" or person.gender == "Child M")]
        totalListMarriedRural += [person.assessment for person in settlement.people if (person.gender == "Married M" or person.gender == "Married F")]


    # This keeps track of the total number of settlements and the average number of inhabitants therein
    numberInhabitants_175 += inhabitants1377_17dot5
    numberInhabitants_10 += inhabitants1377_10
    numberInhabitants_25 += inhabitants1377_25
    

    # Take the data points that are within the range of inhabitants
    binsForCalculation = np.round(10**middle_bins).astype(int)
    binsForCalculation = np.ma.compressed(np.ma.masked_where(binsForCalculation < inhabitants1377_10,binsForCalculation))
    binsForCalculation = np.ma.compressed(np.ma.masked_where(binsForCalculation > inhabitants1377_25,binsForCalculation))
    
    two_sigma = (inhabitants1377_25 - inhabitants1377_10)/2
    middle = inhabitants1377_10 + two_sigma
        
    # In this for loop, we calculate the Gini and Theil factors, and wealth shares, for the range of possible inhabitants 
    
    # Because everything is calculated for every bin of calculation, we divide over the
    # number of calculating bins
    
    gini_temp = []
    n_temp = []
    weight_temp = []
    percent_temp = []
    tenpercent_temp = []
    bottomfiftypercent_temp = []
    topfiftypercent_temp = []
    n_list_percent_temp = []
    n_list_tenpercent_temp = []
    temp_share6pence = []
    
    # print("B: " + str(assessmentsWorkingSet))
    for _ in range(int(number_of_loops/len(binsForCalculation))):
        # Check if the lost assessments need to be reconstructed
        assessmentsWorkingSet = ReconstructLostAssessments(settlement)
        # print("C: "+ str(assessmentsWorkingSet))
        # Add the 20% measurement uncertainty to each assessment
        assessmentsWorkingSet = assessmentsWorkingSet*np.random.normal(1,0.2, len(assessmentsWorkingSet))
        # print("D: "+ str(assessmentsWorkingSet))
        
        for k in binsForCalculation:
            # Add the extra poverty assessments and calculate the gini's
            temporaryAssessmentsWorkingSet = np.append(assessmentsWorkingSet, amountPovertyAssessment*np.ones(k - len(assessmentsWorkingSet)))
            # Calculate the Gini value
            gini_temp.append(Gini(temporaryAssessmentsWorkingSet))
            n_temp.append(k)
            weight_temp.append(1/int(number_of_loops/len(binsForCalculation)))
            
            # Calculate the wealth shares
            sortedTemporaryAssessmentsWorkingSet = np.sort(temporaryAssessmentsWorkingSet)
            toptenpercent = int(len(sortedTemporaryAssessmentsWorkingSet)/10)
            bottomfiftypercent = int(len(sortedTemporaryAssessmentsWorkingSet)/2)
            tenpercent_temp.append(sortedTemporaryAssessmentsWorkingSet[-toptenpercent:].sum()/sortedTemporaryAssessmentsWorkingSet.sum())
            bottomfiftypercent_temp.append(sortedTemporaryAssessmentsWorkingSet[:bottomfiftypercent].sum()/sortedTemporaryAssessmentsWorkingSet.sum())
            topfiftypercent_temp.append(sortedTemporaryAssessmentsWorkingSet[-bottomfiftypercent:-toptenpercent].sum()/sortedTemporaryAssessmentsWorkingSet.sum())
            
            n_list_tenpercent_temp.append(len(sortedTemporaryAssessmentsWorkingSet))
              
            # If above 99 people, calculate the top 1 percent
            if len(sortedTemporaryAssessmentsWorkingSet) > 99:
                toponepercent = int(len(sortedTemporaryAssessmentsWorkingSet)/100) #note that this always rounds down
                percent_temp.append(sortedTemporaryAssessmentsWorkingSet[-toponepercent:].sum()/sortedTemporaryAssessmentsWorkingSet.sum())
                n_list_percent_temp.append(len(sortedTemporaryAssessmentsWorkingSet))
        
    # Add everything that has been calculated above to the correct arrays
    settlement.giniArray = np.array(gini_temp)
    settlement.nArray =  np.array(n_temp)
    settlement.weightsArray = np.array(weight_temp)
    weightArrayOnePercent = np.concatenate((weightArrayOnePercent, np.ones(len(n_list_percent_temp))/number_of_loops/len(n_list_percent_temp)))
    weightArray = np.concatenate((weightArray, np.array(weight_temp)))
    
    # I NEED TO CHANGE THE NAMES BELOW
    list_top_one_percent = np.concatenate((list_top_one_percent,percent_temp))
    list_top_ten_percent = np.concatenate((list_top_ten_percent,tenpercent_temp))
    list_bottom_fifty_percent = np.concatenate((list_bottom_fifty_percent, bottomfiftypercent_temp))
    list_top_fifty_percent = np.concatenate((list_top_fifty_percent, topfiftypercent_temp))
    n_list_top_one_percent = np.concatenate((n_list_top_one_percent,n_list_percent_temp))
    n_list_top_ten_percent = np.concatenate((n_list_top_ten_percent,n_list_tenpercent_temp))

print("Done! Let's start plotting")

# THE NORMALISATION OF THE FIRST PLOT IS NOW HARD-CODED IN, THIS SHOULD BE IMPROVED
fig = plt.figure(figsize = (10,12.66))

gs = fig.add_gridspec(4,1, wspace=0)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[1, 0])
ax3 = fig.add_subplot(gs[2, 0])
ax4 = fig.add_subplot(gs[3, 0])

listie = [ax1, ax2, ax3]

plt.rc('axes', axisbelow=True)
plt.rcParams.update({'font.size': 16})

counter = 0
indEmpl = 0
indGenderEmpl = 0

number_of_xticks += 1


for settlement in reorderedSettlementList[-number_of_xticks:]:
    
    if counter == 0:
        
        handle1 = ax1.scatter(counter,np.mean(totalListMarriedRural), color = 'r', label = "Married", s = 50)
        handle2 = ax1.scatter(counter,np.mean(totalListUnmarriedMenRural), color = 'b', marker = '^', label = "Unm. man", s = 50)
        handle3 = ax1.scatter(counter,np.mean(totalListUnmarriedWomenRural), color = 'g', marker = 'v', label = "Unm. woman", s = 50)
    
    else:
        
        ind = -number_of_xticks + counter
        
        handle1 = ax1.scatter(counter, averageListMarried[ind], color = 'r', label = "Married", s = 50)
        handle2 = ax1.scatter(counter, averageListUnmarriedMen[ind], color = 'b', marker = '^', label = "Unm. man", s = 50)
        handle3 = ax1.scatter(counter, averageListUnmarriedWomen[ind], color = 'g', marker = 'v', label = "Unm. woman", s = 50)
       
        minimum = min(averageListMarried[ind],min(averageListUnmarriedMen[ind], averageListUnmarriedWomen[ind]))
        maximum = max(averageListMarried[ind],max(averageListUnmarriedMen[ind], averageListUnmarriedWomen[ind]))
        ax1.vlines(counter, minimum, maximum, color='k', linewidth = 0.5, zorder = 0)
        
        
        handle4 = ax2.scatter(counter, averageListMarriedFiltered[ind], color = 'r', label = "Married", s = 50)
        handle5 = ax2.scatter(counter, averageListUnmarriedMenFiltered[ind], color = 'b', marker = '^', label = "Unm. man", s = 50)
        handle6 = ax2.scatter(counter, averageListUnmarriedWomenFiltered[ind], color = 'g', marker = 'v', label = "Unm. woman", s = 50)
       
        minimum = min(averageListMarriedFiltered[ind],min(averageListUnmarriedMenFiltered[ind], averageListUnmarriedWomenFiltered[ind]))
        maximum = max(averageListMarriedFiltered[ind],max(averageListUnmarriedMenFiltered[ind], averageListUnmarriedWomenFiltered[ind]))
        ax2.vlines(counter, minimum, maximum, color='k', linewidth = 0.5, zorder = 0)
        
    
        employersInSettlement = sum(np.array([person.employer for person in settlement.people]))
        employeesInSettlement = sum(np.array([person.employee for person in settlement.people]))
        
        if employersInSettlement > 4 and employeesInSettlement > 4:
             handle7 = ax3.scatter(counter, wealthEmployersArray[indEmpl], color = 'r', label = "Employer", s = 50)
             handle8 = ax3.scatter(counter, wealthEmployeesArray[indEmpl], color = 'g', marker = 'v', label = "Employee", s = 50)
             handle9 = ax3.scatter(counter, wealthNeitherEmployerEmployeeArray[indEmpl], color = 'b', marker = '^', label = "Neither", s = 50)
         
             minimum = min(wealthEmployersArray[indEmpl],min(wealthEmployeesArray[indEmpl], wealthNeitherEmployerEmployeeArray[indEmpl]))
             maximum = max(wealthEmployersArray[indEmpl],max(wealthEmployeesArray[indEmpl], wealthNeitherEmployerEmployeeArray[indEmpl]))
             ax3.vlines(counter, minimum, maximum, color='k', linewidth = 0.5, zorder = 0)
             indEmpl = indEmpl + 1
             
        
        femaleEmployeesInSettlement = sum(np.array([person.employee for person in settlement.people if person.gender[-1] == "F"]))
        maleEmployeesInSettlement = sum(np.array([person.employee for person in settlement.people if person.gender[-1] == "M"]))
    
        if femaleEmployeesInSettlement > 2 and maleEmployeesInSettlement > 2:
    
            handle10 = ax4.scatter(counter, wealthFemaleEmployeesArray[indGenderEmpl], color = 'g', marker = 'v', label = "Female employee", s = 50)
            handle11 = ax4.scatter(counter, wealthMaleEmployeesArray[indGenderEmpl], color = 'b', marker = '^', label = "Male employee", s = 50)
           
            minimum = min(wealthFemaleEmployeesArray[indGenderEmpl],wealthMaleEmployeesArray[indGenderEmpl])
            maximum = max(wealthFemaleEmployeesArray[indGenderEmpl],wealthMaleEmployeesArray[indGenderEmpl])
            ax4.vlines(counter, minimum, maximum, color='k', linewidth = 0.5, zorder = 0)
            
            indGenderEmpl = indGenderEmpl + 1
        
    counter += 1
    
 
ax1.set_xlim(-1,number_of_xticks)
ax2.set_xlim(-1,number_of_xticks)
ax3.set_xlim(-1,number_of_xticks)
ax4.set_xlim(-1,number_of_xticks)

settlementsXAxis = [str(settlement.name) + " (" + str(settlement.averageAdultInhabitants) + ")" for settlement in reorderedSettlementList[-number_of_xticks:]]

ax1.set_xticks([],[])
ax2.set_xticks([],[])
ax3.set_xticks([],[])
ax4.set_xticks(np.arange(0,number_of_xticks), settlementsXAxis, rotation = 90, fontsize = 14)

ax1.set_yticks([1/2,8/12,10/12,1,14/12,16/12],["6d","8d","10d","1s","1s2d","1s4d"])
ax2.set_yticks([1/2,8/12,10/12,1,14/12],["6d","8d","10d","1s","1s2d"])
ax3.set_yticks([1/2,1,3/2,2,5/2],["6d","1s","1s6d","2s","2s6d"])
ax4.set_yticks([4/12,1/2,8/12,10/12,1],["4d","6d","8d","10d","1s"])

ax1.set_ylim(5/12,17/12)
ax2.set_ylim(5/12,15/12)
ax3.set_ylim(4/12,31/12)
ax4.set_ylim(3/12,13/12)

ax1.grid(axis = 'y')
ax2.grid(axis = 'y')
ax3.grid(axis = 'y')
ax4.grid(axis = 'y')

ax1.set_ylabel("Average tax assessment")
ax2.set_ylabel("Average tax assessment")
ax3.set_ylabel("Average tax assessment")
ax4.set_ylabel("Average tax assessment")
ax4.set_xlabel("Largest settlements [ascending order]")


ax1.legend(handles = [handle1,handle2,handle3], ncols = 3)
ax2.legend(handles = [handle4,handle6,handle5], ncols = 3)
ax3.legend(handles = [handle7,handle8,handle9], ncols = 3)
ax4.legend(handles = [handle10,handle11], ncols = 2)

plt.savefig("bigplot_characteristics.pdf",bbox_inches = "tight")
plt.show()


plt.rcParams.update({'font.size': 12})
plt.rcParams.update({"figure.figsize": (10, 4)})

plt.rcParams.update({'font.size': 16})

fig = plt.figure(figsize = (12,12))

plt.subplot(2,2,1)

plt.rcParams.update({'font.size': 20})

# The top 1 percent of a settlement
plt.hist2d(n_list_top_one_percent,list_top_one_percent*100,bins=[10**logbins,np.linspace(0,30,num = 100)],
           cmin = 0.0001, weights=weightArrayOnePercent, cmap = "viridis_r")
plt.xscale('log')
plt.xlim(100,max(10**logbins))
plt.ylabel('Share wealth owned top 1%')
plt.xlabel("Number of inhabitants aged 15 and over")
plt.grid(which = "major", axis="x", zorder = -1)
plt.grid(which = "minor", axis = "x", linestyle = "--", alpha = 0.3)
plt.grid(which = "major", axis = "y")
plt.xlim(100,10000)
# plt.colorbar(label = "Density")
# ax = plt.gca()
# ax.set_facecolor("lightgrey")
# plt.colorbar(location= 'right')
plt.tight_layout()
# plt.savefig("toponepercent.pdf")
# plt.show()


plt.subplot(2,2,2)

# The top ten percent
plt.hist2d(n_list_top_ten_percent,list_top_ten_percent*100,bins=[10**logbins,np.linspace(0,60,num = 100)],
           cmin = 0.001, weights=weightArray, cmap = "viridis_r")
plt.xscale('log')
plt.ylabel('Share wealth owned top 10%')
plt.xlabel("Number of inhabitants aged 15 and over")
# plt.colorbar(label = "Density")
# plt.tight_layout()
# ax = plt.gca()
# ax.set_facecolor("lightgrey")
plt.grid(which = "major", axis="x", zorder = -1)
plt.grid(which = "minor", axis = "x", linestyle = "--", alpha = 0.3)
plt.grid(which = "major", axis = "y")
plt.xlim(10,10000)
plt.tight_layout()
# plt.savefig("toptenpercent.pdf")
# plt.show()


# The bottom 50 percent of a settlement
plt.subplot(2,2,3)
plt.hist2d(n_list_top_ten_percent,list_bottom_fifty_percent*100,bins=[10**logbins,np.linspace(0,40,num = 100)],
           cmin = 0.001, weights=weightArray, cmap = "viridis_r")
plt.xscale('log')
plt.ylabel('Share wealth owned bottom 50%')
plt.xlabel("Number of inhabitants aged 15 and over")
# plt.colorbar()#label = "Density")
# plt.colorbar()
plt.grid(which = "major", axis="x", zorder = -1)
plt.grid(which = "minor", axis = "x", linestyle = "--", alpha = 0.3)
plt.grid(which = "major", axis = "y")
plt.xlim(10,10000)
plt.ylim(10,35)
plt.tight_layout()
ax = plt.gca()
# ax.set_facecolor("lightgrey")
# plt.tight_layout()
# plt.savefig("bottomfiftypercent.pdf")
# plt.show()

# The top 50-10 pecent
plt.subplot(2,2,4)
h, _, _, im = plt.hist2d(n_list_top_ten_percent,list_top_fifty_percent*100,bins=[10**logbins,np.linspace(0,80,num = 100)],
                cmin = 0.001, weights=weightArray, cmap = "viridis_r")
plt.xscale('log')
plt.ylabel('Share wealth owned top 50%-10%')
plt.xlabel("Number of inhabitants aged 15 and over")
# plt.colorbar()#label = "Density")
plt.tight_layout()
plt.grid(which = "major", axis="x", zorder = -1)
plt.grid(which = "minor", axis = "x", linestyle = "--", alpha = 0.3)
plt.grid(which = "major", axis = "y")
plt.xlim(10,10000)
plt.ylim(20,80)
ax = plt.gca()

largest_value = np.max(h[h>0])
smallest_value = np.min(h[h>0])

fig.subplots_adjust(right = 0.8)
cbar_ax = fig.add_axes([0.85, 0.15, 0.02, 0.7])
cbar = fig.colorbar(im, cax=cbar_ax, shrink = 0.1,ticks = [smallest_value,largest_value])
cbar.ax.set_yticklabels(['0','1'])

# ax.set_facecolor("lightgrey")
# plt.tight_layout()
# plt.savefig("topfiftypercent.pdf")
# cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
# fig.colorbar(pcm1, ax=[ax1, ax2], shrink=0.8)
plt.savefig("bigplot.pdf", bbox_inches = "tight")
 
plt.figure(figsize = (10,7))

plt.scatter(np.arange(len(theilListMarried)), theilListMarried, color = 'r', label = "Married", s = 50)
plt.scatter(np.arange(len(theilListMarried)), theilListUnmarriedMen, color = 'b', label = "Unm. Men", s = 50, marker = '^')
plt.scatter(np.arange(len(theilListMarried)), theilListUnmarriedWomen, color = 'g', label = "Unm. Women", s = 50, marker = 'v')
plt.scatter(np.arange(len(theilListMarried)), theilListTotal, color = 'k', label = "Total", s = 50, marker = '*')

for ind in range(len(theilListMarried)):
    minimum = min(theilListMarried[ind],min(theilListUnmarriedWomen[ind], theilListUnmarriedMen[ind]))
    maximum = max(theilListMarried[ind],max(theilListTotal[ind], theilListUnmarriedMen[ind]))
    plt.vlines(ind, minimum, maximum, color='k', linewidth = 0.5, zorder = 0)

plt.ylabel(r"Theil index $T$ [nats]")
plt.xlabel(r"Largest settlements [ascending order]")
plt.grid(axis="y")

plt.xticks(np.arange(len(theilListMarried)), [settlement.name for settlement in reorderedSettlementList[-len(theilListMarried):]], rotation = 90, fontsize = 14)
plt.tight_layout()

plt.legend()
plt.savefig('theilGender.pdf')

listCounties = [settlement.county for settlement in reorderedSettlementList]


# Determine the number of unique counties in the data
counties = Counter(listCounties).keys()
countiesValues = Counter(listCounties).values()
counties, countiesValues = zip(*sorted(zip(counties,countiesValues)))

# If this is set to True, make the Gini plots for every specific county

# newCountyList = []
if True:
    counter = 0
    cdfList = []
    xList = []
    for county in counties:
        # if len([settlement for settlement in reorderedSettlementList if settlement.county == county]) < 10:
        #     continue
        # newCountyList.append(county)
        if counter == 0:
            fig = plt.figure(figsize = (10,15))

            gs = fig.add_gridspec(4,1, height_ratios=[1, 1, 1,1], hspace = 0)
            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = fig.add_subplot(gs[1, 0])
            ax3 = fig.add_subplot(gs[2, 0])
            ax4 = fig.add_subplot(gs[3, 0])
            
            axlist = [ax1,ax2,ax3,ax4]
            
        plt.rc('axes', axisbelow=True)
        tempGini = np.concatenate([settlement.giniArray for settlement in reorderedSettlementList if settlement.county == county]).ravel()
        tempN =  np.concatenate([settlement.nArray for settlement in reorderedSettlementList if settlement.county == county]).ravel()
        tempWeight =  np.concatenate([settlement.weightsArray for settlement in reorderedSettlementList if settlement.county == county]).ravel()
        
        # plt.hist(temp_gini, bins = 20)
        _, _, _, im = axlist[counter].hist2d(tempN, tempGini, bins=[10**logbins,np.linspace(0.3,0.6,num = 100)],cmin = 0.001, weights=tempWeight, cmap = "viridis_r")
        
        fig.colorbar(im, ax=axlist[counter], pad=0.02)
        
        # plt.xlabel("Number of inhabitants aged 15 and over")
        axlist[counter].set_ylabel("Gini index " + county)
        axlist[counter].set_xlabel("Number of inhabitants aged 15 and over")
        axlist[counter].set_xscale('log')
        # plt.title(county)
        axlist[counter].grid(which = "major", axis="x", linestyle = "--", zorder = -1)
        axlist[counter].grid(which = "minor", axis = "x", linestyle = "--", alpha = 0.3)
        axlist[counter].grid(which = "major", axis = "y", linestyle = "--")
        axlist[counter].set_xlim(10,10000)
        axlist[counter].set_ylim(0.3,0.5999)
        
        if counter != 3:
            axlist[counter].tick_params(labelbottom=False)
        
        counter += 1
        if counter > 3:
            counter = 0
            plt.savefig("Hinterlandplots\plot2_" + county + '.pdf', bbox_inches = "tight")
            plt.show()
