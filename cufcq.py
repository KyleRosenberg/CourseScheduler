import pandas as pd
import statsmodels.api as sm
import scipy.stats as stats
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import json
import base64

#[val for val in dfResults.columns.values if val[:3]=='Avg'] +

GRADE_MAP = {
    'A': 96,
    'A-': 92,
    'B+': 88,
    'B': 85,
    'B-': 82,
    'C+': 78,
    'C': 75,
    'C-': 72,
    'D+': 68,
    'D': 65,
    'F': 62,
    'P': 85 #We'll say passing a P/F is equivalent to a B
}

#scores should be a pd.Series with one row
def INVERSE_GRADE_MAP(scores):
    score = scores.values[0]
    if (score>96):
        return 'A'
    for k in GRADE_MAP:
        if GRADE_MAP[k]-score<2:
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
        inputs = []
        outputs = []
        for e in oldclasslist:
            inputs.append(self.getAvgStats(e)[1])
            outputs.append({'Grade': GRADE_MAP[e['Grade']]})
        dfInputs = pd.DataFrame(inputs)
        dfOutput = pd.DataFrame(outputs)
        model = sm.OLS(dfOutput, dfInputs).fit()
        for c in potentialclasslist:
            results.append({'code': c['code'], 'prediction': self.predictClassGrade(model, c)})
        return json.dumps(results)

    def predictClassGrade(self, model, cls):
        toPredict = self.getAvgStats({'Subject': cls['code'][:4], 'Course':cls['code'][-4:]})
        dfTargetM = pd.DataFrame(toPredict[1], index=[0])
        resultM = model.predict(dfTargetM)
        dfTargetL = pd.DataFrame(toPredict[0], index=[0])
        resultL = model.predict(dfTargetL)
        dfTargetH = pd.DataFrame(toPredict[2], index=[0])
        resultH = model.predict(dfTargetH)
        return self.getDistributionGraph(resultM, resultL, resultH, model.bse.sum(), cls)

    def getDistributionGraph(self, median, lq, uq, std, cls):
        plt.clf()
        median = min(max(0, median[0]), 100)
        lower = min(max(0, median - 3*std), 100)
        upper = min(max(0, median + 3*std), 100)
        x = np.linspace(lower, upper, 1000)
        y = stats.norm.pdf(x, median, std)
        plt.plot(x, y)
        plt.fill_between(x, 0, y)

        plt.title('Predicted grade for ' + str(cls['code']))

        ret = getPlotPic()
        plt.clf()
        return ret.decode('utf8')

    def getAvgStats(self, courseDict):
        dfCourseHistory = self.fcq_data.loc[(self.fcq_data['Subject'].astype(str)==courseDict['Subject'])&(self.fcq_data['Course'].astype(str)==str(courseDict['Course']))]
        #dfInstructorHistory = self.fcq_data.loc[self.fcq_data['Instructor_Name'].astype(str)==courseDict['Instructor_Name']]
        dfRelevantCourse = dfCourseHistory[['AvgHrsPerWk', 'AvgPriorInt', 'AvgChallenge', 'AvgLearned', 'AvgCourse', 'Std_Dev_Course']]
        #dfRelevantInstructor = dfInstructorHistory[['AvgHrsPerWk', 'AvgInstrEffect', 'AvgAvailability', 'AvgChallenge', 'AvgLearned', 'AvgInstrRespect', 'AvgInstructor', 'Std_Dev_Instr']]
        courseAvg = dfRelevantCourse.median().to_dict()
        course5P = dfRelevantCourse.quantile(0.05).to_dict()
        course95P = dfRelevantCourse.quantile(0.95).to_dict()
        courseStd = dfRelevantCourse.std().to_dict()
        #instructorAvg = dfRelevantInstructor.median().to_dict()
        return [course5P, courseAvg, course95P, courseStd]
        '''
        avgs = instructorAvg
        for k in courseAvg:
            if k in avgs:
                avgs[k] = (avgs[k]+courseAvg[k])/2
            else:
                avgs[k] = courseAvg[k]
        return avgs
        '''

def getPlotPic():
    from io import BytesIO
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    import base64
    figdata_png = base64.b64encode(figfile.getvalue())
    return figdata_png
