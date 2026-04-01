
ClashRoyale-Bot-V2 - v1 ClashRoyale-Bot-V2.0
==============================

This dataset was exported via roboflow.com on March 27, 2026 at 7:19 PM GMT

Roboflow is an end-to-end computer vision platform that helps you
* collaborate with your team on computer vision projects
* collect & organize images
* understand and search unstructured image data
* annotate, and create datasets
* export, train, and deploy computer vision models
* use active learning to improve your dataset over time

For state of the art Computer Vision training notebooks you can use with this dataset,
visit https://github.com/roboflow/notebooks

To find over 100k other datasets and pre-trained models, visit https://universe.roboflow.com

The dataset includes 4786 images.
Cards-hp-bar-towers-units are annotated in YOLO26 format.

The following pre-processing was applied to each image:
* Auto-orientation of pixel data (with EXIF-orientation stripping)
* Resize to 640x640 (Stretch)

The following augmentation was applied to create 3 versions of each source image:
* 50% probability of horizontal flip
* Randomly crop between 0 and 10 percent of the image
* Random brigthness adjustment of between -15 and +15 percent
* Random Gaussian blur of between 0 and 1.3 pixels
* Salt and pepper noise was applied to 1.45 percent of pixels


