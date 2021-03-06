import sys
import shelve
import datetime
import matplotlib.pyplot as plt
import csv_TPattern
import ast
import bisect
import csv
from csv_TPattern import ObservationPeriod, Interval, EventType

DATAFILE  = 'fakesoccerdata.csv'
DATAFILE_CLASSIFICATION = 'fakesoccerdata_classification.csv'

p_value_threshold = .01
WINDOW = 48
laplace = 1 #prior on N_b per observation period
KL_CUTOFF = .1 #2.706 #chi-squared with df=1 and alpha=.10
LIMIT_INFREQUENT_EVENTS = 1 #false or a support threshold
LIMIT_INFREQUENT_PAIRS = 1 #false or a support threshold
OUTPUT_DATA_FILE = 'outputdata.csv'

def printParameters():
	print '''\
	\nParameters:\
	\nLimit Infrequent Events: {0}\
	\nLimit Infrequent Pairs: {1}\
	\nPrune KL-Divergence: {2}\
	\nWindow: {3}\
	\nLaplace Pseudocounts: {4}\
	\nP-value Threshold: {5}\
	\n'''.format(LIMIT_INFREQUENT_EVENTS,LIMIT_INFREQUENT_PAIRS, KL_CUTOFF, WINDOW, laplace, p_value_threshold)

def main(args):

	# get things ready
	start = datetime.datetime.now()
	print "Starting at {0}...\n".format(start)
	sys.stdout.flush()

	printParameters()

	tpattern = csv_TPattern.TPattern(datafile=DATAFILE,
									datafile_classification=DATAFILE_CLASSIFICATION,
									limit_infrequent_events=LIMIT_INFREQUENT_EVENTS,
									limit_infrequent_pairs=LIMIT_INFREQUENT_PAIRS,
									window=WINDOW,
									kl_cutoff=KL_CUTOFF)
	
	tpattern.getEventTypesAndOPs()
	patterns_checked = 0

	
	while tpattern.candidatePatterns:
		patterns_checked +=1
		candidatePattern = tpattern.candidatePatterns.pop(0)
		print "Found:{0} Checked:{1} Candidates:{2}  {3}".format(len(tpattern.t_patterns_found), patterns_checked, len(tpattern.candidatePatterns), candidatePattern)


		intervals = []
		observation_periods_seen = set()

		N_a=0
		with open(tpattern.datafile, 'rb') as f:

			for i in xrange(len(tpattern.observation_periods)):
				op = tpattern.observation_periods[i]
				N_b=0
				tmp_intervals = []
				
				for index1,event1 in enumerate(op):
					eventid1,claimnumber1,ts1_begin,ts1_end,event_type1 = event1
					ts1_end = int(ts1_end)

					op_T = int(op[-1][2]) - int(op[0][2]) +1


					if candidatePattern.first_event_type==event_type1:
						#print "e1: {0}".format(event_type1)
						N_a+=1
						FOUND_ONE_B=False
						


						for index2,event2 in enumerate(op):
							if FOUND_ONE_B: break
							eventid2,claimnumber2,ts2_begin,ts2_end,event_type2 = event2
							ts2_begin = int(ts2_begin)
							if index2>index1 and ts2_begin>ts1_end and candidatePattern.last_event_type==event_type2:

								
								timedelta = ts2_begin-ts1_end +1
								


								if timedelta>WINDOW:
									FOUND_ONE_B=True
									continue
								
								N_b +=1
								FOUND_ONE_B=True
								tmp_intervals.append((timedelta, op_T, eventid1, eventid2, claimnumber1))
								

	
				for tmp_interval in tmp_intervals:
					timedelta, T, first_id, last_id, observation_period = tmp_interval
					interval = Interval(timedelta=timedelta, N_b=int(N_b), T=WINDOW, first_id=first_id, last_id=last_id, observation_period=observation_period, observation_period_T=T)
					intervals.append(interval)


			intervals = sorted(intervals)

			N_ab, critical_interval = tpattern.lookForCriticalIntervals(intervals, N_a, candidatePattern, p_value_threshold)
			
			sys.stdout.flush()


	print "\nChecked {0} patterns.".format(patterns_checked)
	sys.stdout.flush()

	tpattern.completenessCompetition(tpattern.t_patterns_found, OUTPUT_DATA_FILE)

	stop = datetime.datetime.now()
	print "\nFinished at {0}!\nTotal Time: {1}".format(stop, stop-start)


if __name__ == "__main__":
	main(sys.argv)