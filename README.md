# Health-app
# My Health Card

My Health Card is a Django-based web Electronic Medical Record (EMR) with an integrated AI chest X‑ray (CXR) classification pipeline. Built as a final year project to centralize patient records, streamline hospital workflows (admin / doctor / nurse / lab / radiography), and assist radiologists with an automated DenseNet121-based CXR classifier.

## Key features

- Role-based access control for Admin, Doctor, Nurse/HA, Lab Technician, Radiographer, Patient
- Patient profile creation and appointment management
- Vitals entry with BMI auto-calculation and history view
- Doctor consultation module: complaints, physical exam, medications, diagnoses, treatment plans
- Investigation workflow: request → lab/radiology upload → doctor review
- Radiology image upload with filename handling and storage
- AI chest X‑ray prediction endpoint (returns top‑5 probabilities) integrated into the radiology review flow
- MySQL-backed relational schema (appointments, investigations, lab/radio results, vitals)
- Extensive unit and system tests using the Django test framework

## Architecture & tech stack

- Frontend: HTML5, CSS3, JavaScript, Bootstrap (templates)
- Backend: Python, Django (views, templates, role logic, file handling)
- Database: MySQL (models for users, patients, appointments, investigations, results, vitals)
- AI model: DenseNet121 (fine-tuned; CheXpert pre-weights referenced), PyTorch inference pipeline
- File storage: Django FileSystemStorage (radiology images)
- Testing: Django built-in testing framework (unit + system test cases included in repo)

## High-level flow

1. User logs in → role-based dashboard
2. Doctor creates requests → investigation entries created
3. Radiographer uploads CXR image → stored and linked to investigation
4. Predict endpoint loads model and image → returns JSON top‑k predictions → saved as metadata

## Installation & quick start

Prerequisites

- Python 3.8+ (recommended)
- MySQL server
- Virtual environment tool (venv / pipenv)
- GPU optional for faster AI inference; CPU supported

Basic steps (adapt paths and secrets to your environment):

```bash
# Clone the repo and enter project root
git clone https://github.com/<owner>/Health-app.git
cd Health-app

# Create and activate virtual environment
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Configure MySQL:
# - create database
# - update Django DATABASES in settings.py or provide env vars

# Run migrations and create superuser
python manage.py migrate
python manage.py createsuperuser

# Collect static files (if deploying)
python manage.py collectstatic

# Start development server
python manage.py runserver
```

Run tests

```bash
python manage.py test
```

Unit tests cover appointment creation, vitals entry, medication handling, role redirection, and mock-prediction scenarios.

## AI model

- Model architecture: DenseNet121 fine-tuned for multi-class CXR classification (project trains / uses pre-trained CheXpert weights and ChestX‑ray14-like datasets)
- Output: classification among 15 classes (14 pathologies + no findings). Predict endpoint sorts probabilities and returns top 5 as percentages.

Important:
- Place the trained PyTorch model file (.pth/.pt) into the path expected by settings or the view (see settings.ML_MODEL_PATH or README section in repo).
- Ensure torchvision and torch are installed and that the model device selection in the predict view is correct.

Guidance for reproducing training (if training code included):
- Prepare dataset with correct label mapping and image preprocessing (resize, normalize with ImageNet/CheXpert stats)
- Fine-tune DenseNet121 using transfer learning, validate on hold-out radiologist-annotated splits
- Export model weights for inference (torch.save state_dict or full model)

Dataset references used during project work / evaluation:
- ChestX‑ray14 (Wang et al., 2017)
- CheXpert weights for transfer learning

Note: The repository includes inference code and expects the trained model binary to be added by the user (models not committed for size and licensing reasons).

## File storage & radiology images

Radiology images are uploaded using Django's FileSystemStorage. Filenames are managed and stored in the investigation/radiology models and linked to the relevant investigation entries.

## Database schema

The project uses a MySQL-backed relational schema that includes tables/models for:
- Users (roles and permissions)
- Patients
- Appointments
- Investigations
- Lab results and radiology results
- Vitals and vitals history

## Contributing

Issues and pull requests are welcome. Suggested workflow:

1. Fork the repository
2. Create a feature branch
3. Open a pull request with a clear description and test coverage
4. Add unit tests for new functionality where appropriate
5. Keep migrations consistent and document schema changes

## Known limitations

- AI model performance depends on training data and label quality; the model is an assistive tool and not a replacement for clinical decision-making
- No automatic external interoperability (HL7/FHIR) implemented yet
- Currently web-based; mobile app and telemedicine integration planned as future work

## Future work

- Add FHIR compatibility and external EHR integration
- Improve AI (multi-modal, uncertainty estimates, explainability maps)
- Add performance/load tests and role-based audit logging for compliance

## License & contact

- Project owner / author: Sheikh Md Abid (Student ID: 22068727)
- License: Please add a license file in the repository (e.g., MIT or preferred institutional license)

For questions or collaboration: open an issue in the repository or add contact details in the repo profile.
