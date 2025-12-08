"""
Knowledge Base Module for BRIDGE AI
Handles document upload, processing, and retrieval
"""

import os
from typing import Dict, Any, List, Optional
import json


class KnowledgeBase:
    """Manages AI knowledge base with document storage and retrieval"""
    
    def __init__(self, database):
        self.database = database
    
    def upload_pdf(self, filepath: str) -> Dict[str, Any]:
        """
        Upload and process a PDF file
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            Result dictionary with success status
        """
        try:
            import PyPDF2
            
            filename = os.path.basename(filepath)
            
            # Extract text from PDF
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                content = []
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    content.append(text)
                
                full_content = "\n\n".join(content)
            
            # Save to database
            metadata = {
                'pages': num_pages,
                'file_size': os.path.getsize(filepath)
            }
            
            self.database.save_document(
                filename=filename,
                file_type='pdf',
                content=full_content,
                metadata=metadata
            )
            
            return {
                'success': True,
                'message': f'Uploaded {filename} ({num_pages} pages)',
                'pages': num_pages
            }
            
        except ImportError:
            return {
                'success': False,
                'message': 'PyPDF2 not installed. Run: pip install PyPDF2'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error uploading PDF: {str(e)}'
            }
    
    def upload_docx(self, filepath: str) -> Dict[str, Any]:
        """
        Upload and process a Word document
        
        Args:
            filepath: Path to DOCX file
            
        Returns:
            Result dictionary with success status
        """
        try:
            import docx
            
            filename = os.path.basename(filepath)
            
            # Extract text from DOCX
            doc = docx.Document(filepath)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            full_content = "\n\n".join(paragraphs)
            
            # Save to database
            metadata = {
                'paragraphs': len(paragraphs),
                'file_size': os.path.getsize(filepath)
            }
            
            self.database.save_document(
                filename=filename,
                file_type='docx',
                content=full_content,
                metadata=metadata
            )
            
            return {
                'success': True,
                'message': f'Uploaded {filename} ({len(paragraphs)} paragraphs)',
                'paragraphs': len(paragraphs)
            }
            
        except ImportError:
            return {
                'success': False,
                'message': 'python-docx not installed. Run: pip install python-docx'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error uploading DOCX: {str(e)}'
            }
    
    def upload_text(self, filepath: str) -> Dict[str, Any]:
        """
        Upload a text file
        
        Args:
            filepath: Path to text file
            
        Returns:
            Result dictionary with success status
        """
        try:
            filename = os.path.basename(filepath)
            
            # Read text file
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Save to database
            metadata = {
                'lines': len(content.split('\n')),
                'file_size': os.path.getsize(filepath)
            }
            
            self.database.save_document(
                filename=filename,
                file_type='txt',
                content=content,
                metadata=metadata
            )
            
            return {
                'success': True,
                'message': f'Uploaded {filename}',
                'lines': metadata['lines']
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error uploading text file: {str(e)}'
            }
    
    def upload_file(self, filepath: str) -> Dict[str, Any]:
        """
        Auto-detect file type and upload
        
        Args:
            filepath: Path to file
            
        Returns:
            Result dictionary
        """
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.pdf':
            return self.upload_pdf(filepath)
        elif ext in ['.docx', '.doc']:
            return self.upload_docx(filepath)
        elif ext in ['.txt', '.md']:
            return self.upload_text(filepath)
        else:
            return {
                'success': False,
                'message': f'Unsupported file type: {ext}. Supported: PDF, DOCX, TXT, MD'
            }
    
    def get_all_documents(self) -> List[Dict]:
        """Get list of all documents in knowledge base"""
        return self.database.get_all_documents()
    
    def search(self, query: str) -> List[Dict]:
        """
        Search documents for relevant content
        
        Args:
            query: Search query
            
        Returns:
            List of matching documents with excerpts
        """
        results = self.database.search_documents(query)
        
        formatted_results = []
        for filename, content in results:
            # Find query in content and extract context
            query_lower = query.lower()
            content_lower = content.lower()
            
            pos = content_lower.find(query_lower)
            if pos != -1:
                # Extract 200 chars before and after
                start = max(0, pos - 200)
                end = min(len(content), pos + len(query) + 200)
                excerpt = content[start:end]
                
                formatted_results.append({
                    'filename': filename,
                    'excerpt': excerpt,
                    'position': pos
                })
        
        return formatted_results
    
    def get_relevant_context(self, user_question: str, max_docs: int = 3) -> str:
        """
        Get relevant document context for AI based on user question
        
        Args:
            user_question: User's question
            max_docs: Maximum number of documents to include
            
        Returns:
            Formatted context string
        """
        # Extract keywords from question
        keywords = [word for word in user_question.lower().split() 
                   if len(word) > 3 and word not in ['what', 'how', 'when', 'where', 'which', 'that', 'this', 'have', 'with']]
        
        if not keywords:
            return ""
        
        # Search for each keyword
        all_results = []
        for keyword in keywords[:3]:  # Use top 3 keywords
            results = self.search(keyword)
            all_results.extend(results)
        
        if not all_results:
            return ""
        
        # Remove duplicates and limit
        seen_files = set()
        unique_results = []
        for result in all_results:
            if result['filename'] not in seen_files:
                unique_results.append(result)
                seen_files.add(result['filename'])
                if len(unique_results) >= max_docs:
                    break
        
        # Format context
        context = "\n\n" + "="*80 + "\n"
        context += "KNOWLEDGE BASE - RELEVANT DOCUMENTS\n"
        context += "="*80 + "\n\n"
        
        for result in unique_results:
            context += f"**Source: {result['filename']}**\n\n"
            context += result['excerpt'] + "\n\n"
            context += "-"*80 + "\n\n"
        
        return context
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Delete a document from knowledge base
        
        Args:
            filename: Name of file to delete
            
        Returns:
            Result dictionary
        """
        try:
            self.database.delete_document(filename)
            return {
                'success': True,
                'message': f'Deleted {filename}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deleting document: {str(e)}'
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge base"""
        docs = self.get_all_documents()
        
        total_size = sum(len(doc['content']) for doc in docs)
        
        by_type = {}
        for doc in docs:
            file_type = doc['file_type']
            by_type[file_type] = by_type.get(file_type, 0) + 1
        
        return {
            'total_documents': len(docs),
            'total_size_chars': total_size,
            'by_type': by_type,
            'documents': [{'filename': doc['filename'], 'type': doc['file_type'], 
                          'upload_date': doc['upload_date']} for doc in docs]
        }
