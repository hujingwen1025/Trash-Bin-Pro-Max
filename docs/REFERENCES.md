# Related chats and references

Links were collected in the project chats on 19-20 November 2026. External
availability and product details can change. Historical advice is not a purchase
confirmation, manufacturing release, or statement of current local sorting rules.

## Conversation sources

- [Mechanical design and manufacturing chat](thread://01a1edb2-1868-7cc0-9733-c179a83bb8f7?hostId=remote-control%3Aenv_e_6ae46ba5bb84832c98c65a829a96233f)
  — available export: [Markdown](history/mechanical-chat.md), [JSON](history/mechanical-chat.json).
- [Materials discussion: Rubber Feet Dimensions](chatgpt-conversation://6afe6bfd-4834-83ec-81c1-1622c30e01e9)
  — available export: [Markdown](history/materials-chat.md), [JSON](history/materials-chat.json).
- [Camera, datasets, and AI training chat](thread://01a1f3fd-7133-7a81-8893-be2fb0e45797?hostId=local)
  — available export: [Markdown](history/vision-chat.md), [JSON](history/vision-chat.json).

## Datasets

| Dataset | Authoritative reference | Role discussed |
|---|---|---|
| HGI-30 | [Dataset DOI](https://doi.org/10.5281/zenodo.4646699), [paper](https://arxiv.org/html/2202.11878v1) | User-selected; 18,000 images across 30 household-trash classes |
| TrashNet | [Authors' repository](https://github.com/garythung/trashnet), [authors' download page](https://huggingface.co/datasets/garythung/trashnet) | Simple six-class material baseline; original dataset has 2,527 images |
| RealWaste | [UCI dataset](https://archive.ics.uci.edu/dataset/908/realwaste) | Nine material categories including food organics, 4,752 images |
| TACO | [Authors' repository](https://github.com/pedropro/TACO), [paper](https://arxiv.org/abs/2003.06975) | Detection/segmentation of litter in contextual scenes |

The HGI-30 Zenodo link could not be opened through the browsing tool during
the initial lookup, but its DOI was verified in the paper; the user subsequently
confirmed downloading it. No verified HGI-30-trained model-weight download was
found. Public dataset material labels do not replace local disposal rules.

## Camera and training documentation

- [Raspberry Pi camera hardware and viewing angles](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [Camera Module 3](https://www.raspberrypi.com/documentation/accessories/camera-module-3.html)
- [Raspberry Pi AI Camera deployment](https://www.raspberrypi.com/documentation/accessories/ai-camera.html)
- [Seeed reCamera custom classification](https://wiki.seeedstudio.com/train_classification_model_online/)
- [Edge Impulse image classification](https://docs.edgeimpulse.com/tutorials/end-to-end/image-classification)
- [Teachable Machine image training implementation](https://github.com/googlecreativelab/teachablemachine-community/blob/master/libraries/image/src/teachable-mobilenet.ts)
- [Apple Metal/MPS for PyTorch](https://developer.apple.com/metal/pytorch/)
- [PyTorch MPS backend](https://docs.pytorch.org/docs/stable/notes/mps.html)
- [Torchvision EfficientNet-B0](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html)

## Earlier manufacturing research

The materials chat suggested Unionfab, 快印中国, RapidDirect, JLC, and PP-sheet
fabricators as possible quotation sources. The latest R06 plan instead reflects
the user's actual conversation with a board supplier. No supplier contact or
purchase was performed in the AI chat. Consult the preserved materials messages
for the original research rather than treating those recommendations as accepted
quotes.
