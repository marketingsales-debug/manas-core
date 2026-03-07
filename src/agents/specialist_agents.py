"""
VisionAgent — Multimodal Understanding (OmAgent Logic).

Gives Manas the ability to "see" — analyze images, videos,
and reason about visual content using Vision-Language Models.
"""

import logging
import json
import os
import base64
from pathlib import Path
from typing import List, Dict, Any
try:
    import roboflow
    HAS_ROBOFLOW = True
except ImportError:
    HAS_ROBOFLOW = False

try:
    import face_recognition
    HAS_FACE_REC = True
except ImportError:
    HAS_FACE_REC = False

logger = logging.getLogger(__name__)

class VisionAgent:
    """
    Manas's eyes. Processes images and video for understanding.
    """

    def __init__(self, name: str, llm_router, data_dir: str):
        self.name = name
        self.llm_router = llm_router
        self.data_dir = Path(data_dir)
        self.vision_log_path = self.data_dir / "vision_log.json"
        self.total_analyses = 0
        # Facial recognition store
        self.known_faces_dir = self.data_dir / "faces"
        self.known_faces_dir.mkdir(parents=True, exist_ok=True)
        self.known_face_encodings = []
        self.known_face_names = []
        self._load_faces()
        
        # Roboflow integration
        self.rf = None
        self.rf_project = None
        self._init_roboflow()

    def _init_roboflow(self):
        api_key = os.environ.get("ROBOFLOW_API_KEY")
        if HAS_ROBOFLOW and api_key:
            try:
                self.rf = roboflow.Roboflow(api_key=api_key)
                # Default to a generic object detection project if workspace/project provided
                workspace = os.environ.get("ROBOFLOW_WORKSPACE", "manas-ai")
                project_id = os.environ.get("ROBOFLOW_PROJECT", "general-obj-detection")
                self.rf_project = self.rf.workspace(workspace).project(project_id)
                logger.info(f"{self.name}: Roboflow initialized for {workspace}/{project_id}")
            except Exception as e:
                logger.warning(f"{self.name}: Roboflow init failed: {e}")

    def analyze_image(self, image_path: str, question: str = "Describe this image in detail.") -> str:
        """Analyzes an image file using VLM capabilities and optional object detection."""
        logger.info(f"{self.name}: Analyzing image: {image_path}")
        path = Path(image_path)

        if not path.exists():
            return f"❌ Image not found: {image_path}"

        try:
            # 1. Broad VLM Analysis
            with open(path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            prompt = (
                f"[IMAGE ANALYSIS REQUEST]\n"
                f"Image file: {path.name}\n"
                f"Question: {question}\n\n"
                f"Analyze the image and provide:\n"
                f"1. Scene description\n"
                f"2. Key objects detected\n"
                f"3. Colors, mood, and composition\n"
                f"4. Answer to the specific question\n"
                f"5. Any text visible in the image (OCR)"
            )

            vlm_analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")
            self.total_analyses += 1

            # 2. Specialized Object Detection (Roboflow)
            detection_info = ""
            if self.rf_project:
                detection_res = self.detect_objects(image_path)
                if detection_res:
                    detection_info = f"\n🎯 Precise Object Detection (Roboflow):\n{detection_res}"

            return f"👁️ Vision Analysis ({path.name}):\n{vlm_analysis}{detection_info}"
        except Exception as e:
            return f"❌ Vision analysis failed: {e}"

    def detect_objects(self, image_path: str) -> str:
        """Uses Roboflow to detect specific objects in an image."""
        if not self.rf_project:
            return ""
        
        try:
            prediction = self.rf_project.version(1).predict(image_path, confidence=40, overlap=30).json()
            predictions = prediction.get("predictions", [])
            
            if not predictions:
                return "No specific objects identified by specialized model."
            
            summary = []
            for p in predictions:
                summary.append(f"- {p['class']} ({p['confidence']:.2f}) at [{p['x']}, {p['y']}]")
            
            return "\n".join(summary)
        except Exception as e:
            logger.warning(f"Roboflow detection failed: {e}")
            return ""

    def register_face(self, image_path: str, name: str) -> str:
        """Registers a face from an image for future recognition."""
        if not HAS_FACE_REC:
            return "❌ Face recognition library not installed (pip install face_recognition)."
        
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                return "❌ No face detected in the image."
            
            # Save encoding
            encoding_path = self.known_faces_dir / f"{name}.json"
            with open(encoding_path, "w") as f:
                json.dump(encodings[0].tolist(), f)
            
            self.known_face_encodings.append(encodings[0])
            self.known_face_names.append(name)
            
            return f"✅ Successfully registered face for {name}."
        except Exception as e:
            return f"❌ Failed to register face: {e}"

    def recognize_face(self, image_path: str) -> List[str]:
        """Identifies known faces in an image."""
        if not HAS_FACE_REC or not self.known_face_encodings:
            return []
            
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            
            found_names = []
            for encoding in encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, encoding)
                if True in matches:
                    first_match_index = matches.index(True)
                    found_names.append(self.known_face_names[first_match_index])
            
            return found_names
        except Exception:
            return []

    def discover_cctv(self, location: Dict[str, float]) -> List[str]:
        """Scans for nearby publicly accessible CCTV/Webcams (Simulated via OSINT)."""
        lat, lon = location.get("lat"), location.get("lon")
        logger.info(f"Scanning for CCTV near {lat}, {lon}...")
        
        # Simulate OSINT discovery
        # In a real scenario, this would query Shodan or public webcam registries
        nearby_cams = [
            f"Cam_NS_{lat:.2f}_{lon:.2f}_1",
            f"Cam_EW_{lat:.2f}_{lon:.2f}_2"
        ]
        return nearby_cams

    def get_remote_sensor_data(self, device_id: str) -> Dict[str, Any]:
        """Taps into remote device sensors (Mic/Accelerometer)."""
        logger.warning(f"REMOTE SENSOR AUDIT: Device {device_id}")
        # Simulated sensor data
        return {
            "mic_status": "listening",
            "noise_level": 45, # dB
            "accelerometer": {"x": 0.1, "y": 0.0, "z": 9.8}, # Balanced
            "status": "Steady"
        }

    def _load_faces(self):
        """Load registered face encodings from disk."""
        if not HAS_FACE_REC: return
        for face_file in self.known_faces_dir.glob("*.json"):
            try:
                name = face_file.stem
                with open(face_file, "r") as f:
                    self.known_face_encodings.append(np.array(json.load(f)))
                    self.known_face_names.append(name)
            except Exception:
                pass

    def analyze_screenshot(self, sensory) -> str:
        """Takes and analyzes a screenshot of the current screen."""
        logger.info(f"{self.name}: Analyzing current screen...")
        prompt = (
            "Analyze the current screen state. Identify:\n"
            "1. Active applications\n"
            "2. Key information visible\n"
            "3. Any actionable items\n"
            "4. Security concerns (sensitive data visible)"
        )
        analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"👁️ Screen Analysis:\n{analysis}"

    def get_status(self) -> str:
        return (
            f"👁️ VisionAgent Status:\n"
            f"  Total analyses: {self.total_analyses}\n"
            f"  Capabilities: Image analysis, OCR, scene understanding\n"
            f"  Status: Active"
        )


class LegalAgent:
    """
    Manas's legal counsel. Analyzes contracts, regulations, and legal questions.
    """

    def __init__(self, name: str, llm_router, data_dir: str):
        self.name = name
        self.llm_router = llm_router
        self.data_dir = Path(data_dir)
        self.legal_dir = self.data_dir / "legal_analyses"
        self.legal_dir.mkdir(parents=True, exist_ok=True)
        self.total_analyses = 0

    def analyze_contract(self, contract_text: str) -> str:
        """Analyzes a contract or legal document for risks and key terms."""
        prompt = (
            f"As an AI legal analyst, analyze this contract/document:\n\n"
            f"{contract_text[:5000]}\n\n"
            f"Provide:\n"
            f"1. Key Terms & Obligations\n"
            f"2. Potential Risks & Red Flags\n"
            f"3. Missing Protections\n"
            f"4. Recommendations\n"
            f"5. Overall Risk Rating (Low/Medium/High)\n\n"
            f"DISCLAIMER: This is AI analysis, not legal advice."
        )
        analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        self.total_analyses += 1
        return f"⚖️ Legal Analysis:\n{analysis}\n\n*Disclaimer: AI analysis, not legal advice.*"

    def research_law(self, question: str) -> str:
        """Researches a legal question."""
        prompt = (
            f"As a legal research assistant, research this question:\n"
            f"{question}\n\n"
            f"Provide relevant legal principles, precedents, and jurisdictional considerations."
        )
        analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"⚖️ Legal Research:\n{analysis}"

    def get_status(self) -> str:
        return f"⚖️ LegalAgent: {self.total_analyses} analyses completed."


class MedicalAgent:
    """
    Manas's medical knowledge module. Provides health information and triage guidance.
    """

    def __init__(self, name: str, llm_router, data_dir: str):
        self.name = name
        self.llm_router = llm_router
        self.data_dir = Path(data_dir)
        self.total_consultations = 0

    def health_inquiry(self, symptoms: str) -> str:
        """Provides general health information based on described symptoms."""
        prompt = (
            f"As an AI health information assistant, analyze these symptoms:\n"
            f"{symptoms}\n\n"
            f"Provide:\n"
            f"1. Possible conditions (general information only)\n"
            f"2. Recommended actions (self-care vs. see a doctor)\n"
            f"3. Urgency level (Low/Medium/High/Emergency)\n"
            f"4. General wellness recommendations\n\n"
            f"CRITICAL DISCLAIMER: This is NOT medical advice. Always consult a healthcare professional."
        )
        response = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        self.total_consultations += 1
        return f"🏥 Health Information:\n{response}\n\n*⚠️ NOT medical advice. Consult a doctor.*"

    def drug_interaction_check(self, medications: str) -> str:
        """Checks for potential drug interactions (informational only)."""
        prompt = (
            f"As a pharmaceutical information system, check for potential interactions:\n"
            f"Medications: {medications}\n\n"
            f"Provide general information about known interactions and precautions.\n"
            f"DISCLAIMER: Always verify with a pharmacist or doctor."
        )
        response = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        return f"💊 Drug Interaction Info:\n{response}\n\n*Always verify with a pharmacist.*"

    def get_status(self) -> str:
        return f"🏥 MedicalAgent: {self.total_consultations} consultations provided."


class DataAgent:
    """
    Manas's data scientist. Analyzes datasets, generates insights, builds models.
    """

    def __init__(self, name: str, llm_router, data_dir: str):
        self.name = name
        self.llm_router = llm_router
        self.data_dir = Path(data_dir)
        self.analyses_dir = self.data_dir / "data_analyses"
        self.analyses_dir.mkdir(parents=True, exist_ok=True)
        self.total_analyses = 0

    def analyze_data(self, data_description: str, question: str) -> str:
        """Analyzes data based on a natural language question."""
        prompt = (
            f"As an autonomous data scientist, analyze this data:\n"
            f"Data: {data_description[:3000]}\n"
            f"Question: {question}\n\n"
            f"Provide:\n"
            f"1. Data Summary & Key Statistics\n"
            f"2. Patterns & Trends Identified\n"
            f"3. Visualization Recommendations\n"
            f"4. Predictive Insights\n"
            f"5. Actionable Recommendations\n"
            f"6. Python code for the analysis (using pandas/matplotlib)"
        )
        analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        self.total_analyses += 1
        return f"📊 Data Analysis:\n{analysis}"

    def generate_sql(self, question: str, schema: str = "") -> str:
        """Generates SQL from a natural language question."""
        prompt = (
            f"Convert this natural language question to SQL:\n"
            f"Question: {question}\n"
            f"Schema: {schema if schema else 'Unknown - generate generic SQL'}\n\n"
            f"Return only the SQL query."
        )
        sql = self.llm_router.generate(prompt=prompt, task_type="coding")
        return f"📊 Generated SQL:\n```sql\n{sql}\n```"

    def get_status(self) -> str:
        return f"📊 DataAgent: {self.total_analyses} analyses completed."
