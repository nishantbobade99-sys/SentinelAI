import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import timm
from sklearn.model_selection import KFold
from torch.cuda.amp import GradScaler, autocast
import matplotlib.pyplot as plt
# Remove torch.utils.tensorboard dependency if not strictly needed or handle gracefully
try:
    from torch.utils.tensorboard import SummaryWriter
except ImportError:
    SummaryWriter = None

class ImageDeepfakeDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples = []
        
        # Expecting directory structure:
        # data/image_dataset/real/
        # data/image_dataset/fake/
        real_dir = os.path.join(root_dir, 'real')
        fake_dir = os.path.join(root_dir, 'fake')
        
        if os.path.exists(real_dir):
            for f in os.listdir(real_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    self.samples.append((os.path.join(real_dir, f), 0.0))
                    
        if os.path.exists(fake_dir):
            for f in os.listdir(fake_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    self.samples.append((os.path.join(fake_dir, f), 1.0))
                    
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
            
        return image, torch.tensor([label], dtype=torch.float32)

def train_model():
    dataset_dir = 'data/image_dataset'
    weights_path = 'weights/image_model.pth'
    
    if not os.path.exists(os.path.join(dataset_dir, 'real')) and not os.path.exists(os.path.join(dataset_dir, 'fake')):
        print(f"Error: Dataset directory {dataset_dir} does not contain 'real' and 'fake' subdirectories.")
        print("Please place your images in 'data/image_dataset/real/' and 'data/image_dataset/fake/'.")
        return
        
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    dataset = ImageDeepfakeDataset(dataset_dir, transform=transform)
    if len(dataset) < 10:
        print(f"Error: Found only {len(dataset)} images. Please provide more data for training.")
        return
        
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = timm.create_model('efficientnet_b0', pretrained=True, num_classes=1)
    model = model.to(device)
    
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scaler = GradScaler()
    
    print(f"Starting training on {len(dataset)} images over 5 epochs...")
    model.train()
    
    for epoch in range(5):
        running_loss = 0.0
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            
            with autocast():
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            running_loss += loss.item()
            
        print(f"Epoch {epoch+1}/5, Loss: {running_loss/len(dataloader):.4f}")
        
    os.makedirs('weights', exist_ok=True)
    torch.save(model.state_dict(), weights_path)
    print(f"Training complete. Weights saved to {weights_path}.")

if __name__ == "__main__":
    train_model()
