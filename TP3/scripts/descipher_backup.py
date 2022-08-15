import sys
import pickle

def main():
	with open(sys.argv[1], 'rb') as f:
		data = pickle.load(f)
	print(data["middleware"])

if __name__ == "__main__":
	main()
	