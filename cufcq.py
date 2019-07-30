import pandas as pd
import statsmodels.api as sm
import json

#[val for val in dfResults.columns.values if val[:3]=='Avg'] +

GRADE_MAP = {
    'A': 4,
    'A-': 3.7,
    'B+': 3.3,
    'B': 3,
    'B-': 2.7,
    'C+': 2.3,
    'C': 2,
    'C-': 1.7,
    'D+': 1.3,
    'D': 1,
    'F': 0,
    'P': 3 #We'll say passing a P/F is equivalent to a B
}

#scores should be a pd.Series with one row
def INVERSE_GRADE_MAP(scores):
    score = scores.values[0]
    if (score>4):
        return 'A'
    for k in GRADE_MAP:
        if GRADE_MAP[k]-score<=0.2:
            return k
    return 'F'

class FCQAnalyzer:

    def __init__(self):
        self.reloadDataframe()

    def reloadDataframe(self):
        print('Loading fcqs...')
        self.fcq_data = pd.read_excel("fcq/fcq_2010-2019.xlsx")
        print('Loading fcqs done.')

    def getRows(self, subject, course, term, year):
        dfResults = self.fcq_data.loc[(self.fcq_data['Term'].astype(str)==term)&(self.fcq_data['Year'].astype(str)==year)&(self.fcq_data['Subject'].astype(str)==subject)&(self.fcq_data['Course'].astype(str)==course)]
        dfClean = dfResults[['Term', 'Year', 'Subject', 'Course', 'Section', 'Instructor_Name']]
        arr = dfClean.to_json(orient='records')
        return arr

    def predictMultipleGrades(self, oldclasslist, potentialclasslist):
        results = []
        for c in potentialclasslist:
            results.append({'code': c['code'], 'prediction': self.predictClassGrade(oldclasslist, c)})
        return json.dumps(results)

    def predictClassGrade(self, evidence, cls):
        inputs = []
        outputs = []
        for e in evidence:
            inputs.append(self.getAvgStats(e))
            outputs.append({'Grade': GRADE_MAP[e['Grade']]})
        dfInputs = pd.DataFrame(inputs)
        dfOutput = pd.DataFrame(outputs)
        model = sm.OLS(dfOutput, dfInputs).fit()
        toPredict = self.getAvgStats({'Subject': cls['code'][:4], 'Course':cls['code'][-4:]})
        dfTarget = pd.DataFrame(toPredict, index=[0])
        result = model.predict(dfTarget)
        return INVERSE_GRADE_MAP(result)

    def getAvgStats(self, courseDict):
        dfCourseHistory = self.fcq_data.loc[(self.fcq_data['Subject'].astype(str)==courseDict['Subject'])&(self.fcq_data['Course'].astype(str)==str(courseDict['Course']))]
        #dfInstructorHistory = self.fcq_data.loc[self.fcq_data['Instructor_Name'].astype(str)==courseDict['Instructor_Name']]
        dfRelevantCourse = dfCourseHistory[['AvgHrsPerWk', 'AvgPriorInt', 'AvgChallenge', 'AvgLearned', 'AvgCourse', 'Std_Dev_Course']]
        #dfRelevantInstructor = dfInstructorHistory[['AvgHrsPerWk', 'AvgInstrEffect', 'AvgAvailability', 'AvgChallenge', 'AvgLearned', 'AvgInstrRespect', 'AvgInstructor', 'Std_Dev_Instr']]
        courseAvg = dfRelevantCourse.median().to_dict()
        #instructorAvg = dfRelevantInstructor.median().to_dict()
        return courseAvg
        '''
        avgs = instructorAvg
        for k in courseAvg:
            if k in avgs:
                avgs[k] = (avgs[k]+courseAvg[k])/2
            else:
                avgs[k] = courseAvg[k]
        return avgs
        '''
