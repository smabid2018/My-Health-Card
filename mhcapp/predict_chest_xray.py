import os
import torch
from torchvision import models, transforms
from PIL import Image
import numpy as np

# Define the function to load the model
def load_model(model_path, device):
    model = models.densenet121(weights=None)
    num_ftrs = model.classifier.in_features
    model.classifier = torch.nn.Sequential(torch.nn.Linear(num_ftrs, 15), torch.nn.Sigmoid())
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    return model

# Define the function to preprocess the image
def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(256),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image_path).convert('RGB')
    image = transform(image)
    image = image.unsqueeze(0)  # Add batch dimension
    return image

# Define the function to make a prediction on a single image
def predict_chest_xray(image_path, model_path, device):
    # Load the model
    model = load_model(model_path, device)

    # Preprocess the image
    image = preprocess_image(image_path)
    image = image.to(device)

    # Make prediction
    with torch.no_grad():
        output = model(image)
        prediction = output.cpu().numpy()

    # Define the labels
    labels = ['Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration', 'Mass', 'Nodule', 
              'Pneumonia', 'Pneumothorax', 'Consolidation', 'Edema', 'Emphysema', 'Fibrosis', 
              'Pleural_Thickening', 'Hernia', 'No Finding']

    # Convert prediction to a dictionary with label probabilities
    prediction_dict = {label: float(prob) for label, prob in zip(labels, prediction[0])}

    return prediction_dict

# Set the device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Define the paths
image_path = 'datasets/images_001/images/00000181_038.png'  # Update this path to the image file
model_path = 'best_model.pth'  # Update this path to the trained model file

# Run the prediction
if __name__ == "__main__":
    prediction = predict_chest_xray(image_path, model_path, device)
    print("Predictions for the image:")
    for label, prob in prediction.items():
        print(f"{label}: {prob:.4f}")