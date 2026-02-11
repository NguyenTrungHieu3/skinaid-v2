# AI SYSTEM OVERVIEW

## Problem Introduction

### Context and Motivation

Skin wounds such as abrasions, burns, and bruises are very common and
can lead to infection if not properly treated. However, many people lack
basic first aid knowledge, especially in areas with limited access to
healthcare services. Therefore, a technological solution is needed to
support rapid wound identification and assessment through images. This
is the motivation for the team to build the SkinAid system \-- an AI
application that helps detect, classify wounds, and support users with
initial treatment.

### Problem Statement

The core problem that the research team aims to solve is: \"How to build
an automated system capable of accurately identifying and classifying
common types of skin wounds and assessing their severity through images,
thereby providing appropriate basic first aid guidance for users without
medical expertise?\"

Specifically, the system needs to perform the following tasks:

Task 1: Wound Detection

- Input: Image of skin area potentially wounded

- Output: Determine whether there is a wound in the image

- Additional Output: Exact location of the wound (bounding box) if
  detected

Task 2: Wound Classification

- Input: Image region containing the detected wound

- Output: Wound type (abrasion, burn, bruise)

Task 3: Severity Assessment

- Input: Classified wound

- Output: Severity level (mild, moderate, severe)

### Problem Challenges

The wound detection and classification problem in SkinAid faces many
challenges regarding data, models, and deployment:

#### Data Source Limitations

- **Lack of real medical data**: Due to healthcare privacy constraints
  (HIPAA), the project can only use public datasets from Kaggle and
  Google Images instead of actual medical records from hospitals

- **Inconsistent data quality**: Images from public sources have varying
  resolutions, shooting angles, and lighting conditions, not
  standardized as in medical environments

- **Data imbalance**: Some common wound types (like abrasions) have more
  samples than others (like chemical burns), leading to model bias

- **Lack of diversity**: The current dataset does not fully cover
  variations in ethnicity, age, and wound location on the body

#### Time and Human Resource Limitations:

- **Short development time:** Only 4 months (16 weeks) to complete the
  entire project (data collection, model training, web development,
  testing)

- **Human resources:** Team consists of students with:

<!-- -->

- Limited practical experience

- Part-time availability

- Difficulty implementing complex advanced features

<!-- -->

- **Limited budget:** Must prioritize open-source solutions and free
  cloud credits

#### Infrastructure Limitations:

- Limited GPU (Google Colab/personal machines) reduces training speed
  and makes it difficult to experiment with large models.

#### AI Model Accuracy and Limitations:

- Target accuracy ≥ 65% still carries risk of errors.

- Model only classifies 3 common wound types, not covering complex cases
  like infections, deep cuts, or surgical wounds.

#### Diversity in Wound Morphology and Manifestation:

- The same wound type can vary significantly in shape, size, cause, and
  color over recovery time.

- Some wounds have overlapping characteristics (abrasion with bruising),
  making classification difficult.

#### Safety and Ethical Requirements

- AI results are for reference only, not a substitute for doctor\'s
  assessment; clear warning messages must be ensured.

- Classification errors can lead to inappropriate first aid guidance and
  potential legal liability.

### Why Does the SkinAid Project Need AI/Machine Learning?

SkinAid uses AI/ML, especially Deep Learning models like YOLOv11 and
EfficientNet B0, because this is the only solution that meets the
requirements for wound detection and classification from images \-\-- a
task that traditional methods cannot handle effectively.

#### Meeting Functional Requirements

- AI has the ability to automatically recognize and classify wound
  images (abrasion, bruise, burn) through CNN models.

- Supports wound healing progress tracking by comparing images over time
  and detecting abnormal signs.

#### Meeting Quality Attributes (Non-functional Requirements)

- **Performance:** Deep Learning models optimized for fast inference,
  processing images in about 3-5 seconds, meeting the ≤10 second
  response requirement.

- **Accuracy:** Transfer learning from pretrained models like ImageNet
  helps achieve ≥65% accuracy even with limited medical data.

# DATASET & DATA PREPARATION {#dataset-data-preparation}

## Data Sources

The dataset was collected from multiple public sources to ensure
diversity and quality for the model:

- **Main source**: Roboflow Universe - Medical Wound Dataset

- **Additional sources**: Kaggle, GitHub public repositories, Google
  Images

- **Total number of images:** 2,269 images

<!-- -->

- Training set: 1,583 images (70%)

- Validation set: 456 images (20%)

- Test set: 230 images (10%)

**Wound Type Distribution:**

| **Wound Type**  | **Number of Images** | **Percentage (%)** |
|-----------------|----------------------|--------------------|
| **Burn**        | \~ 500               | \~ 22.04%          |
| **Bruise**      | \~ 500               | \~ 22.04%          |
| **Abrasion**    | \~ 500               | \~ 22.04%          |
| **Normal_Skin** | \~ 769               | \~ 33.89%          |

Severity Levels:

- Mild: \~40%

- Moderate: \~60%

## Data Annotation

### Annotation for YOLO (Object Detection)

YOLO uses bounding box annotation format with structure:

[\<class_id\> \<x_center\> \<y_center\> \<width\> \<height\>]{.mark}

Where:

- class_id: 0 (wound), 1 (no_wound)

- Coordinate values are normalized to \[0, 1\]

Example YOLO annotation file (image_001.txt):

[0 0.512 0.438 0.234 0.187]{.mark}

### Annotation for EfficientNet (Classification)

EfficientNet uses classification label format with structure:

[{wound_type}\_{severity}]{.mark}

Class list:

- burn_mild, burn_moderate_blister, burn_moderate_skintear

- bruise_mild, bruise_moderate

- abrasion_mild, abrasion_moderate

### Tools Used

- Roboflow: Manual annotation for bounding boxes, collaborative
  annotation for team, dataset management, automatic augmentation

## Data Preprocessing & Augmentation {#data-preprocessing-augmentation}

### Preprocessing Techniques

- Auto-Orient

- Resize to 640×640

### Augmentation Techniques

- Flip: Horizontal, Vertical

- Crop: 0% Minimum Zoom, 5% Maximum Zoom

- Rotation: Between -10° and +10°

- Brightness: Between -5% and +5%

- Blur: Up to 1px

- Noise: Up to 0.1% of pixels

Reasons for using augmentation:

- Increase dataset diversity

- Reduce overfitting

- Improve model generalization capability

- Simulate different lighting conditions and shooting angles in practice

### Data Preprocessing & Augmentation pipline {#data-preprocessing-augmentation-pipline}

![pako:eNqd0s9KwzAYAPBXCd-u3UjbtOtyEPbHgyAIw5Orh9B86YJtMrIUdWPP4QP5YmZdHR7Eg4V85PvzSw7pESorETjUTuy25H5dGhK\--WYtXsldK2p8JuPxDVls5p234wen0fjny9Ci7yw3a9zrAxJvSc7o50cIw8CyH1gFWreBCa-tGVqrvnW7eXRCG23qoXyJe\_\_eIJkTpZuGjzBWmVLR3jv7gnxEaZ5X1ZCOX7X0W57s3n7KxSCVUmklr1IpISj9Uy7_LVeDlAylFFeZFGLKsj_l7fedhZz-kLJKs18kROGptATuXYcRtOhacU7heD6zBL_FFkvgYStRia7xJZTmFNhOmCdr22_pbFdvgSvR7EPW7aTwuNIi_AftterQSHRL2xkPPMnT_hDgR3gDHifFJMmTtGAzls2KCN6Bs-kko3HB4mlKWVjpKYJDfyedFCyU2IymIaY0i09fhrrHQQ
(784×57)](media/image1.png){width="5.988096019247594in"
height="0.4365452755905512in"}

**Figure 1: Data Preprocessing and Augmentation Pipeline**

The process includes five sequential stages:

- Raw Image: Original images collected from dataset

- Auto-Orient: Automatically adjust image orientation based on EXIF
  metadata

- Resize to 640×640: Standardize all image sizes to 640×640 pixels

- Augmentation: Apply data augmentation techniques (flip, crop, rotate,
  brightness adjustment, blur, and noise) to increase diversity

- Training: Processed images are fed into the YOLOv11 model for training

# AI PIPELINE ARCHITECTURE

## AI Pipeline Overview

### Main Purpose and Functions

The AI pipeline is built to \"automatically detect and classify wounds\"
from input images. The system operates on a Two-Stage Pipeline model:

| **Stage**   | **Module**      | **Task**                                                  |
|-------------|-----------------|-----------------------------------------------------------|
| **Stage 1** | YOLO v11        | Detect wound locations in images (Object Detection)       |
| **Stage 2** | EfficientNet B0 | Classify wound types and severity levels (Classification) |

Main objectives:

- Automatically identify wound locations in images

- Accurately classify wound types (abrasion, bruise, burn)

- Assess severity levels (mild, moderate, severe)

- Provide confidence score for each result

### Overall Input

| **Attribute**    | **Description**                 |
|------------------|---------------------------------|
| **Format**       | JPEG, PNG                       |
| **Maximum size** | 5MB                             |
| **Data type**    | RGB color image                 |
| **Requirements** | Clear image, wound within frame |

### Output tổng thể (Đầu ra)

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>{</p>
<p>"success": true,</p>
<p>"ai_model_version": "YOLOv11 and EfficientnetB0",</p>
<p>"total_detections": 2,</p>
<p>"processing_time_ms": 450,</p>
<p>"primary_wound_type": "burn",</p>
<p>"detections": [</p>
<p>{</p>
<p>"wound_type": "burn",</p>
<p>"severity": "burn_moderate_blister",</p>
<p>"confidence_score": 0.89,</p>
<p>"bbox": {</p>
<p>"x1": 120,</p>
<p>"y1": 80,</p>
<p>"x2": 350,</p>
<p>"y2": 280</p>
<p>}</p>
<p>}</p>
<p>]</p>
<p>}</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Field Explanations:

- success: Processing status (true/false)

- total_detections: Number of wounds detected

- processing_time_ms: Processing time (milliseconds)

- primary_wound_type: Primary wound type in image

- detections: Detailed list of wounds

### Processing Flow Diagram

![](media/image2.png){width="3.098279746281715in"
height="4.583333333333333in"}

Description of flow:

1.  Receive input image → Check format and size

2.  YOLO v11 → Scan entire image to detect wound regions

3.  Crop detected regions → Cut each bounding box into separate image

4.  EfficientNet B0 → Classify each cropped region

5.  Aggregate results → Return final response

## Module 1: YOLO (Object Detection)

### Role and Functions  {#role-and-functions}

YOLO is used to detect wounds in images, returning location (bounding
box) and confidence for each detected region. The model is suitable for
its fast speed, good accuracy, and ability to handle multiple wounds in
one image.

### Technical Specifications

| **Parameter**            | **Value**               | **Description**            |
|--------------------------|-------------------------|----------------------------|
| **Model**                | YOLO v11                | Version of YOLO            |
| **Model file**           | \`model_2_class_v1.pt\` | Trained weight file        |
| **Confidence threshold** | 0.55 (55%)              | Result filtering threshold |
| **Image size**           | 640 × 640               | Input image size           |
| **Số class**             | 2                       | wound, non-wound           |

### YOLO Input

- Image data in numpy.ndarray format (OpenCV)

- BGR color format

- Image is resized to 640×640 before being fed into model

### Processing Steps

YOLO performs main steps:

1.  **Preprocessing:** Resize and normalize image

2.  **Detection:** Extract features and predict bounding boxes

3.  **Post-processing:** Apply NMS and filter by confidence ≥ 0.55

### YOLO Output

Format bounding box:

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>{</p>
<p>"class_name": "wound", # Tên class phát hiện</p>
<p>"confidence": 0.87, # Độ tin cậy (0.0 - 1.0)</p>
<p>"bbox": [120.5, 80.3, 350.2, 280.1] # [x1, y1, x2, y2]</p>
<p>}</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Where bbox = \[x1, y1, x2, y2\] are coordinates of top-left and
bottom-right corners of detected region (in pixels).

## Module 2: EfficientNet (Classification)

### Role and Functions  {#role-and-functions-1}

EfficientNet B0 is used to classify wound types (abrasion, bruise, burn)
and assess severity levels (mild, moderate). The model was chosen for
its fast speed, lightweight architecture, and effectiveness with
small-scale medical data.

### Technical Specifications

| **Parameter**         | **Value**       | **Description**                     |
|-----------------------|-----------------|-------------------------------------|
| **Model**             | EfficientNet B0 | Lightweight version of EfficientNet |
| **Model file**        | final_model.pth | PyTorch weight file                 |
| **Number of classes** | 7               | 7 wound types/severity levels       |
| **Image size**        | 224 × 224       | Input image size                    |
| **Device**            | CPU             | Inference device                    |

### Input: Cropped Images from YOLO  {#input-cropped-images-from-yolo}

- Images cropped from YOLO (size depends on bounding box)

- Images are resized to 224×224 and normalized according to ImageNet
  standard

### Processing Steps

![](media/image3.png){width="6.496527777777778in"
height="0.9138888888888889in"}

EfficientNet processes images through main steps:

1.  Convert BGR → RGB

2.  Resize 224×224

3.  Normalize

4.  Forward pass through EfficientNet

5.  Softmax → probabilities

6.  Select class with highest probability

### Output: Classification Label and Probability

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p># Returns tuple (severity_class, confidence_score)</p>
<p>("burn_moderate_blister", 0.89)</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### Classification Classes

| **STT** | **Class name**         | **Wound Type** | **Severity** | **Description**                      |
|---------|------------------------|----------------|--------------|--------------------------------------|
| **0**   | abrasion_mild          | Abrasion       | Mild         | Surface abrasion, little bleeding    |
| **1**   | abrasion_moderate      | Abrasion       | Moderate     | Deeper abrasion, more bleeding       |
| **2**   | bruise_mild            | Bruise         | Mild         | Small bruise, light color            |
| **3**   | bruise_moderate        | Bruise         | Moderate     | Large bruise, dark color             |
| **4**   | burn_mild              | Burn           | Mild         | 1st degree burn, red skin            |
| **5**   | burn_moderate_blister  | Burn           | Moderate     | 2nd degree burn, with water blisters |
| **6**   | burn_moderate_skintear | Burn           | Moderate     | 2nd degree burn, skin tear           |

## Machine Learning Model Architecture

![A screenshot of a computer AI-generated content may be
incorrect.](media/image4.png){width="6.358589238845144in"
height="5.368055555555555in"}

**Wound Detection and Classification Model Details**

**1. Data Acquisition and Cleaning**

The dataset consisting of 2,269 wound images was collected from multiple
public sources including Roboflow Universe, Kaggle, and Google Images.
The data cleaning process involved:

- Removing images without target wound classes to maintain dataset focus

- Identifying and eliminating duplicate images to prevent model
  overfitting

- Filtering out blurry or low-quality images to ensure the model learns
  from clear examples

**2. Data Annotation**

Wound images were annotated using Roboflow annotation tools. For the
YOLO detection model, bounding boxes were drawn around wound regions.
For the EfficientNet classification model, images were labeled with
wound types (burn, bruise, abrasion) and severity levels (mild,
moderate). This annotation process provides accurate ground truth data
for supervised learning.

**3. Data Augmentation and Balancing**

To address class imbalances, data augmentation techniques were applied
through Roboflow, including:

- Horizontal and vertical flipping

- Rotation (between -10° and +10°)

- Brightness adjustment (±5%)

- Random blur and noise addition

These techniques help create a balanced dataset and improve model
generalization across all wound types.

**4. Data Splitting**

The final dataset of 2,269 images was split into:

- Training set: 1,583 images (70%)

- Validation set: 456 images (20%)

- Test set: 230 images (10%)

Stratified splitting was used to maintain consistent class distribution
across all sets.

**5. Model Selection and Training**

**YOLOv11 for Object Detection:** After evaluating multiple YOLO
variants (v8, v9, v11, v12), YOLOv11 was selected for its optimal
balance between accuracy and inference speed. The model was trained to
detect wound regions in images and return bounding box coordinates.
Images are resized to 640×640 pixels and normalized to \[0,1\] range
during preprocessing.

**EfficientNet B0 for Classification:** EfficientNet B0 was chosen after
comparing multiple variants (B0, B1, B2, B3) for wound classification.
The model processes cropped wound regions (resized to 224×224 pixels)
and classifies them into wound types (abrasion, bruise, burn) and
severity levels (mild, moderate). Transfer learning from ImageNet
weights helps achieve good performance despite the limited medical
dataset.

**6. Hyperparameter Tuning**

Both models underwent fine-tuning:

- **YOLOv11:** Learning rate scheduling, batch size optimization, and
  confidence threshold tuning (set to 55% minimum)

- **EfficientNet B0:** Learning rate optimization, epoch tuning, and
  dropout rate adjustment to prevent overfitting

**7. Model Integration and Deployment**

The two models work in a pipeline: YOLOv11 first detects and localizes
wound regions, then EfficientNet B0 classifies each detected region.
Both models are saved as PyTorch files (.pt for YOLO, .pth for
EfficientNet) and integrated into a FastAPI backend that handles image
upload, inference coordination, and result delivery with bounding boxes,
classifications, and confidence scores. The system is optimized for
response time under 10 seconds and provides detailed wound analysis
reports for users.

## Step-by-Step Workflow  {#step-by-step-workflow}

### Process Overview  {#process-overview}

The AI pipeline consists of 5 main steps: check input image → detect
wounds → crop detected regions → classify → return JSON results.

### Step-by-Step Description  {#step-by-step-description}

Step 1: Input Image Validation

The system receives user-uploaded images and performs checks:

- Read image file content

- Check valid format (JPEG, PNG)

- Check file size does not exceed 5MB

- Convert image to processable data

**If image is invalid:** Return error message to user.

**Step 2: Wound Detection using YOLO**

Image is fed into YOLO v11 model to scan and search for wound regions:

- YOLO analyzes entire image

- Identifies suspicious wound regions

- Returns bounding box coordinates for each detected region

- Calculates confidence for each region

**If no wound detected:** Return empty result with not found message.

**Step 3: Crop Bounding Box Regions**

For each region detected by YOLO:

- Get bounding box coordinates (x1, y1, x2, y2)

- Crop that region from original image into small image

- Ensure coordinates are within image bounds

Result: List of cropped images, each containing one wound.

**Step 4: Classify Each Cropped Region**

Each cropped image is fed into EfficientNet B0 model:

- Resize image to 224×224 pixels

- Normalize colors according to ImageNet standard

- EfficientNet model classifies wound type and severity level

- Calculate confidence for classification result

Result: Wound type (abrasion/bruise/burn) and severity level
(mild/moderate/severe).

**Step 5: Aggregate and Return Results**

System aggregates all information:

- Combine YOLO results (location) with EfficientNet results
  (classification)

- Determine primary wound type

- Calculate total number of wounds detected

- Record processing time

- Package into JSON response to return to user

### Special Case Handling

| **Case**                    | **Handling**                                       |
|-----------------------------|----------------------------------------------------|
| Image cannot be read        | Return error \"Invalid image format\"              |
| No wound detected           | Return empty list, success = true                  |
| YOLO confidence \< 55%      | Skip that region, do not include in classification |
| Error during classification | Skip error region, continue with other regions     |

## Concrete Illustration Example

### Example 1: Successful Case

Input: Image of burned hand with water blisters

![](media/image5.jpeg){width="2.825757874015748in"
height="1.8422550306211725in"}

Step 1: Receive and Check Input Image

System receives JPG image file, checks format and size → Image is valid

Step 2 - Detection using YOLO:

YOLO detects 2 wound regions and returns results:

- Region 1: bbox \[264, 75, 550, 347\], confidence 0.85

- Region 2: bbox \[151, 259, 289, 409\], confidence 0.80

![](media/image6.png){width="1.8500787401574803in"
height="2.8634372265966754in"}

Step 3 - Crop Bounding Box Regions:

- Crop 2 regions:

<!-- -->

- Crop region 1 from (264, 75) to (550, 347)

  ![A close up of a blister on a person\'s skin AI-generated content may
  be incorrect.](media/image7.jpeg){width="2.181547462817148in"
  height="2.068490813648294in"}

- Crop region 2 from (151, 259) to (289, 409)

  ![Close up of a fingernail AI-generated content may be
  incorrect.](media/image8.jpeg){width="1.5982141294838146in"
  height="1.7438560804899388in"}

Step 4 - Classification using EfficientNet:

- Crop region 1: burn_moderate_blister (confidence: 0.89)

![A screen shot of a computer code AI-generated content may be
incorrect.](media/image9.png){width="3.257296587926509in"
height="2.2347364391951006in"}

- Crop region 2: burn_moderate_blister (confidence: 0.76)

![A screen shot of a computer code AI-generated content may be
incorrect.](media/image10.png){width="3.272275809273841in"
height="2.1663385826771653in"}

Step 5 - Aggregate and Return Results:

![](media/image11.png){width="3.1535837707786527in"
height="3.3864009186351707in"}

Interpretation: System detected 2 burns with 85% and 80% confidence,
classified as moderate burns with water blisters.
