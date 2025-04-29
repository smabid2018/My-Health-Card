import os
import pandas as pd
from sklearn.model_selection import train_test_split
from torchvision import transforms
import torch
from torch.utils.data import Dataset
from PIL import Image

# Define the dataset class
class NIH_Dataset(Dataset):
    def __init__(self, dataframe, image_dir, transform=None):
        self.dataframe = dataframe
        self.image_dir = image_dir
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        img_name = os.path.join(self.image_dir, self.dataframe.iloc[idx, 0])
        image = Image.open(img_name).convert('RGB')
        labels = self.dataframe.iloc[idx, 1:].values.astype('float')
        if self.transform:
            image = self.transform(image)
        return image, torch.tensor(labels)

# Preprocess the dataset and split into train and validation sets
def preprocess_dataset():
    # Path to the dataset CSV file
    csv_file = 'datasets/Data_Entry_2017.csv'
    image_dirs = ['datasets/images_001/images', 'datasets/images_002/images', 
                  'datasets/images_003/images', 'datasets/images_004/images', 
                  'datasets/images_005/images', 'datasets/images_006/images', 
                  'datasets/images_007/images', 'datasets/images_008/images', 
                  'datasets/images_009/images', 'datasets/images_010/images', 
                  'datasets/images_011/images', 'datasets/images_012/images']

    # Read the CSV file
    df = pd.read_csv(csv_file)

    # Split the dataset into training and validation sets
    train_val_list = pd.read_csv('datasets/train_val_list.txt', header=None).iloc[:, 0].tolist()
    test_list = pd.read_csv('datasets/test_list.txt', header=None).iloc[:, 0].tolist()

    train_val_df = df[df['Image Index'].isin(train_val_list)]
    test_df = df[df['Image Index'].isin(test_list)]
    
    train_df, val_df = train_test_split(train_val_df, test_size=0.2, random_state=42)

    # Save the train and validation DataFrames
    train_df.to_csv('train_labels.csv', index=False)
    val_df.to_csv('val_labels.csv', index=False)
    test_df.to_csv('test_labels.csv', index=False)

    print('Dataset preprocessed and split into train, validation, and test sets.')

if __name__ == "__main__":
    preprocess_dataset()