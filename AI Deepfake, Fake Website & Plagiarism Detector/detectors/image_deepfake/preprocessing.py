from torchvision import transforms
from PIL import Image

def get_image_transforms():
    """ImageNet standard transforms"""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

def preprocess_image(image_path):
    """Load and preprocess image for EfficientNet"""
    try:
        img = Image.open(image_path).convert('RGB')
        transform = get_image_transforms()
        img_t = transform(img)
        # Add batch dimension
        img_t = img_t.unsqueeze(0)
        return img_t
    except Exception as e:
        raise ValueError(f"Error preprocessing image: {e}")
