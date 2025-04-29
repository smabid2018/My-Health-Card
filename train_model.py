import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
import pandas as pd
from PIL import Image

# Define the dataset class
class NIH_Dataset(Dataset):
    def __init__(self, dataframe, image_dirs, transform=None):
        self.dataframe = dataframe
        self.image_dirs = image_dirs
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        img_name = self.dataframe.iloc[idx, 0]
        img_path = self._find_image_path(img_name)
        image = Image.open(img_path).convert('RGB')
        labels = self.dataframe.iloc[idx, 1].split('|')
        labels_binary = [1 if label in labels else 0 for label in self._get_all_labels()]
        if self.transform:
            image = self.transform(image)
        return image, torch.tensor(labels_binary, dtype=torch.float32)

    def _find_image_path(self, img_name):
        for image_dir in self.image_dirs:
            img_path = os.path.join(image_dir, img_name)
            if os.path.exists(img_path):
                return img_path
        raise FileNotFoundError(f"Image {img_name} not found in any of the directories.")

    def _get_all_labels(self):
        all_labels = ['Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration', 'Mass', 'Nodule', 
                      'Pneumonia', 'Pneumothorax', 'Consolidation', 'Edema', 'Emphysema', 'Fibrosis', 
                      'Pleural_Thickening', 'Hernia', 'No Finding']
        return all_labels

# Define the training function
def train_model(train_df_path, val_df_path, image_dirs, device, lr=0.001, num_epochs=25):
    # Load the train and validation DataFrames
    train_df = pd.read_csv(train_df_path)
    val_df = pd.read_csv(val_df_path)

    # Define the transformations
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
    train_transforms = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.Resize(256),
        transforms.CenterCrop(256),
        transforms.ToTensor(),
        normalize
    ])
    val_transforms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(256),
        transforms.ToTensor(),
        normalize
    ])

    # Create the datasets and dataloaders
    train_dataset = NIH_Dataset(train_df, image_dirs, transform=train_transforms)
    val_dataset = NIH_Dataset(val_df, image_dirs, transform=val_transforms)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=4)

    # Initialize the model
    model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
    num_ftrs = model.classifier.in_features
    model.classifier = nn.Sequential(nn.Linear(num_ftrs, 15), nn.Sigmoid())  # 15 classes for the labels
    model = model.to(device)

    # Define the loss function and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    # Create log file
    log_file = open('training_logs.txt', 'w')
    log_file.write("Epoch,Training Loss,Validation Loss\n")

    # Training loop
    best_loss = float('inf')
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        for inputs, labels in tqdm(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)
        epoch_loss = running_loss / len(train_loader.dataset)
        print(f'Epoch {epoch}/{num_epochs}, Loss: {epoch_loss}')

        # Validation loop
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for inputs, labels in tqdm(val_loader):
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)
        val_loss /= len(val_loader.dataset)
        print(f'Validation Loss: {val_loss}')

        # Save the best model
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), 'best_model.pth')

        # Log the epoch, training loss, and validation loss
        log_file.write(f"{epoch},{epoch_loss},{val_loss}\n")

    log_file.close()

# Set the device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# List of image directories
image_dirs = ['datasets/images_001/images', 'datasets/images_002/images', 
              'datasets/images_003/images', 'datasets/images_004/images', 
              'datasets/images_005/images', 'datasets/images_006/images', 
              'datasets/images_007/images', 'datasets/images_008/images', 
              'datasets/images_009/images', 'datasets/images_010/images', 
              'datasets/images_011/images', 'datasets/images_012/images']

# Train the model
if __name__ == "__main__":
    print(f'Using device: {device}')
    train_model('train_labels.csv', 'val_labels.csv', image_dirs, device)