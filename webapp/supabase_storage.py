"""
Supabase Storage Integration for BRIA Pixel Playground.

This module handles uploading, downloading, and managing files in Supabase Storage.
"""

import os
import json
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class SupabaseStorage:
    """Handle file storage operations with Supabase."""
    
    BUCKET_NAME = "pixel-art"  # Main bucket for all generated files
    
    def __init__(
        self,
        supabase_url: str = None,
        supabase_key: str = None
    ):
        """
        Initialize Supabase storage client.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/public API key
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase credentials not found. "
                "Set SUPABASE_URL and SUPABASE_KEY in .env file."
            )
        
        # Storage API base URL
        self.storage_url = f"{self.supabase_url}/storage/v1"
        
        # Headers for API requests
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}"
        }
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> bool:
        """Create the storage bucket if it doesn't exist."""
        try:
            # Check if bucket exists
            response = httpx.get(
                f"{self.storage_url}/bucket/{self.BUCKET_NAME}",
                headers=self.headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"[Supabase] Bucket '{self.BUCKET_NAME}' exists")
                return True
            
            # Create bucket if it doesn't exist
            if response.status_code == 404:
                create_response = httpx.post(
                    f"{self.storage_url}/bucket",
                    headers={**self.headers, "Content-Type": "application/json"},
                    json={
                        "id": self.BUCKET_NAME,
                        "name": self.BUCKET_NAME,
                        "public": True  # Make files publicly accessible
                    },
                    timeout=10.0
                )
                
                if create_response.status_code in [200, 201]:
                    print(f"[Supabase] Created bucket '{self.BUCKET_NAME}'")
                    return True
                else:
                    print(f"[Supabase] Failed to create bucket: {create_response.text}")
                    return False
            
            return False
            
        except Exception as e:
            print(f"[Supabase] Error checking/creating bucket: {e}")
            return False
    
    def upload_file(
        self,
        local_path: str,
        remote_path: str = None,
        content_type: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a file to Supabase Storage.
        
        Args:
            local_path: Path to local file
            remote_path: Path in storage (defaults to filename)
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            Dict with file info including public URL, or None on failure
        """
        local_path = Path(local_path)
        
        if not local_path.exists():
            print(f"[Supabase] File not found: {local_path}")
            return None
        
        # Default remote path to filename
        if remote_path is None:
            remote_path = local_path.name
        
        # Auto-detect content type
        if content_type is None:
            suffix = local_path.suffix.lower()
            content_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".svg": "image/svg+xml",
                ".json": "application/json",
                ".webp": "image/webp"
            }
            content_type = content_types.get(suffix, "application/octet-stream")
        
        try:
            with open(local_path, "rb") as f:
                file_data = f.read()
            
            # Upload to Supabase Storage
            response = httpx.post(
                f"{self.storage_url}/object/{self.BUCKET_NAME}/{remote_path}",
                headers={
                    **self.headers,
                    "Content-Type": content_type,
                    "x-upsert": "true"  # Overwrite if exists
                },
                content=file_data,
                timeout=60.0  # Longer timeout for large files
            )
            
            if response.status_code in [200, 201]:
                public_url = self.get_public_url(remote_path)
                print(f"[Supabase] Uploaded: {remote_path}")
                return {
                    "path": remote_path,
                    "public_url": public_url,
                    "size": len(file_data),
                    "content_type": content_type
                }
            else:
                print(f"[Supabase] Upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[Supabase] Upload error: {e}")
            return None
    
    def upload_bytes(
        self,
        data: bytes,
        remote_path: str,
        content_type: str = "application/octet-stream"
    ) -> Optional[Dict[str, Any]]:
        """
        Upload bytes directly to Supabase Storage.
        
        Args:
            data: File content as bytes
            remote_path: Path in storage
            content_type: MIME type
        
        Returns:
            Dict with file info including public URL, or None on failure
        """
        try:
            response = httpx.post(
                f"{self.storage_url}/object/{self.BUCKET_NAME}/{remote_path}",
                headers={
                    **self.headers,
                    "Content-Type": content_type,
                    "x-upsert": "true"
                },
                content=data,
                timeout=60.0
            )
            
            if response.status_code in [200, 201]:
                public_url = self.get_public_url(remote_path)
                print(f"[Supabase] Uploaded bytes: {remote_path}")
                return {
                    "path": remote_path,
                    "public_url": public_url,
                    "size": len(data),
                    "content_type": content_type
                }
            else:
                print(f"[Supabase] Upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[Supabase] Upload error: {e}")
            return None
    
    def upload_json(
        self,
        data: Dict[str, Any],
        remote_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Upload JSON data to Supabase Storage.
        
        Args:
            data: Dictionary to serialize as JSON
            remote_path: Path in storage (should end with .json)
        
        Returns:
            Dict with file info including public URL, or None on failure
        """
        json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        return self.upload_bytes(json_bytes, remote_path, "application/json")
    
    def get_public_url(self, remote_path: str) -> str:
        """
        Get the public URL for a file.
        
        Args:
            remote_path: Path in storage
        
        Returns:
            Public URL string
        """
        return f"{self.supabase_url}/storage/v1/object/public/{self.BUCKET_NAME}/{remote_path}"
    
    def download_file(
        self,
        remote_path: str,
        local_path: str = None
    ) -> Optional[bytes]:
        """
        Download a file from Supabase Storage.
        
        Args:
            remote_path: Path in storage
            local_path: Optional local path to save file
        
        Returns:
            File contents as bytes, or None on failure
        """
        try:
            response = httpx.get(
                f"{self.storage_url}/object/{self.BUCKET_NAME}/{remote_path}",
                headers=self.headers,
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.content
                
                if local_path:
                    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(local_path, "wb") as f:
                        f.write(data)
                    print(f"[Supabase] Downloaded: {remote_path} -> {local_path}")
                
                return data
            else:
                print(f"[Supabase] Download failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[Supabase] Download error: {e}")
            return None
    
    def list_files(
        self,
        prefix: str = "",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List files in the storage bucket.
        
        Args:
            prefix: Filter by path prefix
            limit: Maximum number of results
        
        Returns:
            List of file metadata dictionaries
        """
        try:
            response = httpx.post(
                f"{self.storage_url}/object/list/{self.BUCKET_NAME}",
                headers={**self.headers, "Content-Type": "application/json"},
                json={
                    "prefix": prefix,
                    "limit": limit,
                    "sortBy": {
                        "column": "created_at",
                        "order": "desc"
                    }
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                files = response.json()
                # Add public URLs
                for f in files:
                    if f.get("name"):
                        path = f"{prefix}/{f['name']}" if prefix else f['name']
                        f["public_url"] = self.get_public_url(path)
                return files
            else:
                print(f"[Supabase] List failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[Supabase] List error: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        """
        Delete a file from Supabase Storage.
        
        Args:
            remote_path: Path in storage
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = httpx.delete(
                f"{self.storage_url}/object/{self.BUCKET_NAME}/{remote_path}",
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code in [200, 204]:
                print(f"[Supabase] Deleted: {remote_path}")
                return True
            else:
                print(f"[Supabase] Delete failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[Supabase] Delete error: {e}")
            return False


# Singleton instance for convenience
_storage_instance: Optional[SupabaseStorage] = None


def get_storage() -> Optional[SupabaseStorage]:
    """Get or create the Supabase storage instance."""
    global _storage_instance
    
    if _storage_instance is None:
        try:
            _storage_instance = SupabaseStorage()
        except ValueError as e:
            print(f"[Supabase] Initialization failed: {e}")
            return None
    
    return _storage_instance


def is_storage_enabled() -> bool:
    """Check if Supabase storage is configured and available."""
    return get_storage() is not None
