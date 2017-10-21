# Imports
import os, sys, math
from shutil import copy2, rmtree
import subprocess
from mse import rmsdiff

# Constants
temp_dir = 'tmp'
original_dir = 'original'

# MPSNR settings
window_size = 5
psnr_threshold = 30

class PSNR:
	def __init__(self, path, original):
		global temp_dir

		self.path = path
		self.name = self.path.split('/')[-1:][0].encode('utf-8')
		self.temp_path = './' + temp_dir + '/' + self.name

		self.o_path = original
		self.o_name = self.o_path.split('/')[-1:][0].encode('utf-8')
		self.o_temp_path = './' + original_dir + '/' + self.o_name

		# Values
		# Traditional PSNR
		self.naive_psnr = 0
		# Matched PSNR
		self.mpsnr = 0
		# Distorted frame rate
		self.d_frame_rate = 0
		# Distorted frames psnr
		self.dpsnr = 0
		# Frame loss rate
		self.lost_frame_count = 0
		self.l_rate = 0

		# Metrics
		self.pomos = 0
		self.romos = 0

	def extract_original_ppm(self):
		global original_dir

		# Create temp directory to store ppm
		if os.path.exists(original_dir):
			rmtree(original_dir)
		os.mkdir(original_dir)

		# Copy contents to tmp
		copy2(self.o_path, self.o_temp_path)
		
		# Make per frame ppm in tmp
		cmd = 'mplayer ' + self.o_name + ' -vo pnm -nosound'
		p = subprocess.Popen([cmd], cwd=original_dir, shell=True)
		p.wait()

	def extract_ppm(self):
		global temp_dir

		# Create temp directory to store ppm
		if os.path.exists(temp_dir):
			rmtree(temp_dir)
		os.mkdir(temp_dir)

		# Copy contents to tmp
		copy2(self.path, self.temp_path)
		
		# Make per frame ppm in tmp
		cmd = 'mplayer ' + self.name + ' -vo pnm -nosound'
		p = subprocess.Popen([cmd], cwd=temp_dir, shell=True)
		p.wait()

	def preprocess_ppm(self):
		# Extract original file into frames
		self.extract_original_ppm()

		# Extract file to check into frames
		self.extract_ppm()

	def process_naive_psnr(self):
		global temp_dir
		global original_dir

		# Get list of all frame ppms
		o_frames = os.listdir(original_dir)
		o_frames = filter(lambda x: x != self.o_name, o_frames)
		o_frames.sort()

		frames = os.listdir(temp_dir)
		frames = filter(lambda x: x != self.name, frames)
		frames.sort()

		# MSE
		total_mse = 0

		i = 0
		total = len(frames)
		while i < len(o_frames) and i < len(frames):
			print i,'/',total
			total_mse += rmsdiff(original_dir + '/' + o_frames[i], temp_dir + '/' + frames[i])
			i +=1

		if total_mse == 0:
			p.naive_psnr = 100
		else:
			total_mse = float(total_mse)/i
			p.naive_psnr = 20 * math.log10(255.0 / math.sqrt(total_mse))

	def process_mpsnr(self):
		global window_size
		global psnr_threshold
		global temp_dir
		global original_dir

		# Get list of all frame ppms
		o_frames = os.listdir(original_dir)
		o_frames = filter(lambda x: x != self.o_name, o_frames)
		o_frames.sort()

		frames = os.listdir(temp_dir)
		frames = filter(lambda x: x != self.name, frames)
		frames.sort()

		# Calculate frame loss rate
		self.lost_frame_count = len(o_frames) - len(frames)
		self.l_rate = float(self.lost_frame_count)/len(o_frames)

		# MSE
		total_mse = 0

		# Distorted frames count
		dfr = 0

		# Number of frames taken into account
		numFrames = 0

		total = len(frames)
		for i in range(total):
			print i,'/',total
			max_psnr = 0
			min_mse = sys.maxint
			for j in range(i,i+window_size):
				if j < len(o_frames):
					mse = rmsdiff(original_dir + '/' + o_frames[j], temp_dir + '/' + frames[i])
					psnr = 0
					if mse != 0:
						psnr = 20*math.log(255) - 10*math.log(mse)
					else:
						psnr = 100
					if psnr > max_psnr:
						max_psnr = psnr
						min_mse = mse

			# Distorted frame rate calculation
			if max_psnr < 100:
				dfr += 1
				self.dpsnr += max_psnr

			if max_psnr > 100:
				max_psnr = 100

			if max_psnr > psnr_threshold:
				total_mse += min_mse
				self.mpsnr += max_psnr
			else:
				mse = rmsdiff(original_dir + '/' + o_frames[i], temp_dir + '/' + frames[i])
				psnr = 0
				if mse != 0:
					psnr = 20*math.log(255) - 10*math.log(mse)
				else:
					psnr = 100
				total_mse += mse
				self.mpsnr += psnr

			numFrames += 1

		# Calculate mpsnr
		self.mpsnr = self.mpsnr/numFrames

		# Calculate distorted frame rate
		self.d_frame_rate = float(dfr)/total
		
		# Calculate dPSNR
		if dfr != 0:
			self.dpsnr = float(self.dpsnr)/dfr
		else:
			self.dpsnr = 100

		'''
		if total_mse == 0:
			p.mpsnr = 100
		else:
			total_mse = float(total_mse)/numFrames
			p.mpsnr = 20 * math.log10(255.0 / math.sqrt(total_mse))
		'''

	def process_pomos(self):
		self.pomos = 0.8311 + (0.0392*self.mpsnr)

	def process_romos(self):
		self.romos = 4.367 - ( 0.5040 * (float(self.d_frame_rate)/self.dpsnr) ) - (0.0517 *  self.l_rate)

	def log_result(self):
		line = 'STATS\n'
		line += 'Frames lost : ' + str(self.lost_frame_count) + '\n'
		line += 'Traditional PSNR : ' + str(self.naive_psnr) + '\n'
		line += 'MPSNR : ' + str(self.mpsnr) + '\n'
		line += 'dPSNR : ' + str(self.dpsnr) + '\n\n'
		line += 'METRICS\n'
		line += 'POMOS : ' + str(self.pomos) + '\n'
		line += 'ROMOS : ' + str(self.romos) + '\n'

		print '\nSTATS'
		print 'Frames lost : ',str(self.lost_frame_count)
		print 'Traditional PSNR : ',str(self.naive_psnr)
		print 'MPSNR : ',str(self.mpsnr)
		print 'dPSNR : ',str(self.dpsnr) + '\n'
		print 'METRICS'
		print 'POMOS : ',str(self.pomos)
		print 'ROMOS : ',str(self.romos) 

		f = open('results.txt','w+')
		f.write(line)
		f.close()

	def analyze(self):
		# Create ppm files for both videos
		#self.preprocess_ppm()
		# Calculate naive psnr
		self.process_naive_psnr()
		# Calculate mpsnr
		self.process_mpsnr()
		# Calculates POMOS score
		self.process_pomos()
		# Calculates ROMOS score
		self.process_romos()
		# Log Results
		self.log_result()

if __name__=='__main__':
	# Check for correct input args
	if len(sys.argv) < 3:
		print 'Error. Usage: psnr.py video ref_video'
		exit(0)

	stream_video = sys.argv[1]
	original_video = sys.argv[2]

	# Create PSNR object
	p = PSNR(stream_video, original_video)
	p.analyze()
	