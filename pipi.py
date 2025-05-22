import pickle
with open('frames_cap.pkl', 'rb') as f:
    frames = pickle.load(f)
print(frames[0][1])      # First unit, first frame
print(frames[-1][1])     # First unit, last frame
