"""
Orthanc service for DICOM server integration.
"""

import logging
import httpx
from typing import List, Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class OrthancService:
    """Service for interacting with Orthanc DICOM server."""
    
    def __init__(self):
        self.base_url = settings.orthanc_url
        self.timeout = 30.0
    
    async def get_study_image_urls(self, study_uid: str) -> List[str]:
        """
        Get WADO-RS URLs for all images in a study.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get study information
                response = await client.get(f"{self.base_url}/studies/{study_uid}")
                
                if response.status_code == 404:
                    logger.warning(f"Study not found in Orthanc: {study_uid}")
                    return []
                
                response.raise_for_status()
                study_info = response.json()
                
                image_urls = []
                
                # Get all series in the study
                for series_id in study_info.get("Series", []):
                    series_response = await client.get(f"{self.base_url}/series/{series_id}")
                    series_response.raise_for_status()
                    series_info = series_response.json()
                    
                    # Get all instances in the series
                    for instance_id in series_info.get("Instances", []):
                        # Create WADO-RS URL for the instance
                        wado_url = f"{self.base_url}/wado/studies/{study_uid}/series/{series_id}/instances/{instance_id}"
                        image_urls.append(wado_url)
                
                logger.info(f"Found {len(image_urls)} images for study {study_uid}")
                return image_urls
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting images for study {study_uid}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error getting images for study {study_uid}: {str(e)}")
            return []
    
    async def get_study_thumbnail_url(self, study_uid: str) -> Optional[str]:
        """
        Get thumbnail URL for a study (first image).
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get study information
                response = await client.get(f"{self.base_url}/studies/{study_uid}")
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                study_info = response.json()
                
                # Get first series
                series_list = study_info.get("Series", [])
                if not series_list:
                    return None
                
                first_series = series_list[0]
                series_response = await client.get(f"{self.base_url}/series/{first_series}")
                series_response.raise_for_status()
                series_info = series_response.json()
                
                # Get first instance
                instances = series_info.get("Instances", [])
                if not instances:
                    return None
                
                first_instance = instances[0]
                
                # Create thumbnail URL
                thumbnail_url = f"{self.base_url}/instances/{first_instance}/preview"
                return thumbnail_url
                
        except Exception as e:
            logger.error(f"Error getting thumbnail for study {study_uid}: {str(e)}")
            return None
    
    async def get_study_metadata(self, study_uid: str) -> Optional[Dict[str, Any]]:
        """
        Get complete study metadata from Orthanc.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get study information
                response = await client.get(f"{self.base_url}/studies/{study_uid}")
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                study_info = response.json()
                
                # Get main tags
                main_tags = study_info.get("MainDicomTags", {})
                patient_tags = study_info.get("PatientMainDicomTags", {})
                
                metadata = {
                    "study_uid": study_uid,
                    "study_id": main_tags.get("StudyID"),
                    "study_date": main_tags.get("StudyDate"),
                    "study_time": main_tags.get("StudyTime"),
                    "study_description": main_tags.get("StudyDescription"),
                    "accession_number": main_tags.get("AccessionNumber"),
                    "referring_physician": main_tags.get("ReferringPhysicianName"),
                    "patient_id": patient_tags.get("PatientID"),
                    "patient_name": patient_tags.get("PatientName"),
                    "patient_birth_date": patient_tags.get("PatientBirthDate"),
                    "patient_sex": patient_tags.get("PatientSex"),
                    "series_count": len(study_info.get("Series", [])),
                    "instance_count": study_info.get("CountInstances", 0),
                    "orthanc_id": study_info.get("ID"),
                    "last_update": study_info.get("LastUpdate")
                }
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error getting metadata for study {study_uid}: {str(e)}")
            return None
    
    async def get_series_list(self, study_uid: str) -> List[Dict[str, Any]]:
        """
        Get list of series in a study with metadata.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get study information
                response = await client.get(f"{self.base_url}/studies/{study_uid}")
                
                if response.status_code == 404:
                    return []
                
                response.raise_for_status()
                study_info = response.json()
                
                series_list = []
                
                for series_id in study_info.get("Series", []):
                    series_response = await client.get(f"{self.base_url}/series/{series_id}")
                    series_response.raise_for_status()
                    series_info = series_response.json()
                    
                    main_tags = series_info.get("MainDicomTags", {})
                    
                    series_data = {
                        "series_id": series_id,
                        "series_uid": main_tags.get("SeriesInstanceUID"),
                        "series_number": main_tags.get("SeriesNumber"),
                        "series_description": main_tags.get("SeriesDescription"),
                        "modality": main_tags.get("Modality"),
                        "body_part": main_tags.get("BodyPartExamined"),
                        "instance_count": len(series_info.get("Instances", [])),
                        "thumbnail_url": f"{self.base_url}/series/{series_id}/preview"
                    }
                    
                    series_list.append(series_data)
                
                return series_list
                
        except Exception as e:
            logger.error(f"Error getting series list for study {study_uid}: {str(e)}")
            return []
    
    async def check_orthanc_health(self) -> bool:
        """
        Check if Orthanc server is healthy and accessible.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/system")
                response.raise_for_status()
                
                system_info = response.json()
                logger.info(f"Orthanc health check passed: {system_info.get('Name', 'Unknown')}")
                return True
                
        except Exception as e:
            logger.error(f"Orthanc health check failed: {str(e)}")
            return False
    
    async def get_orthanc_statistics(self) -> Dict[str, Any]:
        """
        Get Orthanc server statistics.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get system information
                system_response = await client.get(f"{self.base_url}/system")
                system_response.raise_for_status()
                system_info = system_response.json()
                
                # Get statistics
                stats_response = await client.get(f"{self.base_url}/statistics")
                stats_response.raise_for_status()
                stats_info = stats_response.json()
                
                return {
                    "name": system_info.get("Name"),
                    "version": system_info.get("Version"),
                    "database_version": system_info.get("DatabaseVersion"),
                    "total_disk_size": stats_info.get("TotalDiskSize"),
                    "total_disk_size_mb": stats_info.get("TotalDiskSizeMB"),
                    "count_patients": stats_info.get("CountPatients"),
                    "count_studies": stats_info.get("CountStudies"),
                    "count_series": stats_info.get("CountSeries"),
                    "count_instances": stats_info.get("CountInstances")
                }
                
        except Exception as e:
            logger.error(f"Error getting Orthanc statistics: {str(e)}")
            return {}
    
    async def search_studies(
        self,
        patient_id: Optional[str] = None,
        study_date: Optional[str] = None,
        modality: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search studies in Orthanc using DICOM query parameters.
        """
        try:
            query_params = {}
            
            if patient_id:
                query_params["PatientID"] = patient_id
            if study_date:
                query_params["StudyDate"] = study_date
            if modality:
                query_params["Modality"] = modality
            
            query_params["Level"] = "Study"
            query_params["Limit"] = limit
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/tools/find",
                    json=query_params
                )
                response.raise_for_status()
                
                study_ids = response.json()
                studies = []
                
                for study_id in study_ids:
                    study_response = await client.get(f"{self.base_url}/studies/{study_id}")
                    study_response.raise_for_status()
                    study_info = study_response.json()
                    
                    main_tags = study_info.get("MainDicomTags", {})
                    patient_tags = study_info.get("PatientMainDicomTags", {})
                    
                    study_data = {
                        "orthanc_id": study_id,
                        "study_uid": main_tags.get("StudyInstanceUID"),
                        "patient_id": patient_tags.get("PatientID"),
                        "study_date": main_tags.get("StudyDate"),
                        "study_description": main_tags.get("StudyDescription"),
                        "modality": main_tags.get("ModalitiesInStudy", "").split("\\")[0] if main_tags.get("ModalitiesInStudy") else "",
                        "series_count": len(study_info.get("Series", [])),
                        "instance_count": study_info.get("CountInstances", 0)
                    }
                    
                    studies.append(study_data)
                
                return studies
                
        except Exception as e:
            logger.error(f"Error searching studies in Orthanc: {str(e)}")
            return []