"""
Azure Cosmos DB service for managing database operations.
"""
from typing import Any, Dict, List, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.container import ContainerProxy
from azure.cosmos.database import DatabaseProxy

from src.models import Conversation, User
from src.utils import LoggerMixin, settings, CosmosBulkOperations


class CosmosDBService(LoggerMixin):
    """Service for interacting with Azure Cosmos DB."""
    
    def __init__(self) -> None:
        """Initialize Cosmos DB client and containers."""
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.conversations_container: Optional[ContainerProxy] = None
        self.users_container: Optional[ContainerProxy] = None
        self.gold_container: Optional[ContainerProxy] = None
        
        if settings.cosmos_endpoint and settings.cosmos_key:
            self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Cosmos DB connection and containers."""
        try:
            self.logger.info("Initializing Cosmos DB connection")
            
            # Create client
            self.client = CosmosClient(
                settings.cosmos_endpoint,
                settings.cosmos_key
            )
            
            # Get or create database
            self.database = self.client.create_database_if_not_exists(
                id=settings.cosmos_database_name
            )
            
            # Get or create containers
            self.conversations_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_container_conversations,
                partition_key=PartitionKey(path="/partitionKey"),
                offer_throughput=400
            )
            
            self.users_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_container_users,
                partition_key=PartitionKey(path="/partitionKey"),
                offer_throughput=400
            )
            
            # Gold container with hierarchical partition key (pkType, pkFilter)
            self.gold_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_container_gold,
                partition_key=PartitionKey(path=["/pkType", "/pkFilter"], kind="MultiHash"),
                offer_throughput=400
            )
            
            self.logger.info("Cosmos DB initialization successful")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise
    
    # Conversation operations
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        try:
            conversation_dict = conversation.to_cosmos_dict()
            self.conversations_container.create_item(body=conversation_dict)
            self.logger.info(f"Created conversation: {conversation.id}")
            return conversation
        except exceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        try:
            item = self.conversations_container.read_item(
                item=conversation_id,
                partition_key=user_id
            )
            return Conversation(**item)
        except exceptions.CosmosResourceNotFoundError:
            self.logger.warning(f"Conversation not found: {conversation_id}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get conversation: {e}")
            raise
    
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update an existing conversation."""
        try:
            conversation_dict = conversation.to_cosmos_dict()
            self.conversations_container.upsert_item(body=conversation_dict)
            self.logger.info(f"Updated conversation: {conversation.id}")
            return conversation
        except Exception as e:
            self.logger.error(f"Failed to update conversation: {e}")
            raise
    
    async def list_conversations(
        self, 
        user_id: str, 
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Conversation]:
        """List conversations for a user."""
        try:
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            
            if status:
                query += " AND c.status = @status"
                parameters.append({"name": "@status", "value": status})
            
            query += " ORDER BY c.updated_at DESC"
            
            items = list(self.conversations_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id,
                max_item_count=limit
            ))
            
            return [Conversation(**item) for item in items]
        except Exception as e:
            self.logger.error(f"Failed to list conversations: {e}")
            raise
    
    # User operations
    async def create_user(self, user: User) -> User:
        """Create a new user."""
        try:
            user_dict = user.to_cosmos_dict()
            self.users_container.create_item(body=user_dict)
            self.logger.info(f"Created user: {user.id}")
            return user
        except exceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        try:
            # Try direct read first (faster if partition key matches)
            try:
                item = self.users_container.read_item(
                    item=user_id,
                    partition_key=user_id
                )
                return User(**item)
            except exceptions.CosmosResourceNotFoundError:
                # If direct read fails, try query (in case partition key doesn't match)
                self.logger.info(f"Direct read failed for user {user_id}, trying query...")
                query = "SELECT * FROM c WHERE c.id = @user_id"
                parameters = [{"name": "@user_id", "value": user_id}]
                
                items = list(self.users_container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                if items:
                    return User(**items[0])
                
                self.logger.warning(f"User not found: {user_id}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        try:
            query = "SELECT * FROM c WHERE c.email = @email"
            parameters = [{"name": "@email", "value": email}]
            
            items = list(self.users_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                return User(**items[0])
            return None
        except Exception as e:
            self.logger.error(f"Failed to get user by email: {e}")
            raise
    
    async def update_user(self, user: User) -> User:
        """Update an existing user."""
        try:
            user_dict = user.to_cosmos_dict()
            self.users_container.upsert_item(body=user_dict)
            self.logger.info(f"Updated user: {user.id}")
            return user
        except Exception as e:
            self.logger.error(f"Failed to update user: {e}")
            raise
    
    # Gold container operations
    async def query_gold_data(
        self, 
        query: str, 
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query against gold data."""
        try:
            self.logger.info(f"Executing Cosmos DB query: {query}")
            if parameters:
                self.logger.info(f"Query parameters: {parameters}")
            
            items = list(self.gold_container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            ))
            self.logger.info(f"Gold data query returned {len(items)} items")
            return items
        except Exception as e:
            self.logger.error(f"Failed to query gold data: {e}")
            raise

    # Bulk operations
    def _get_container(self, container_name: str) -> ContainerProxy:
        """Get container by name."""
        containers = {
            "conversations": self.conversations_container,
            "users": self.users_container,
            "gold": self.gold_container
        }
        container = containers.get(container_name)
        if not container:
            raise ValueError(f"Invalid container name: {container_name}. Valid options: {list(containers.keys())}")
        return container
    
    async def bulk_create_items(
        self, 
        container_name: str, 
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Bulk create items in specified container.
        
        Args:
            container_name: Name of the container ('conversations', 'users', 'gold')
            items: List of items to create
            
        Returns:
            List of successfully created items
        """
        try:
            container = self._get_container(container_name)
            
            # Determine partition key path based on container
            if container_name == 'gold':
                partition_key_path = 'pkType,pkFilter'  # Hierarchical partition key
            else:
                partition_key_path = 'partitionKey'  # Single partition key
            
            result = await CosmosBulkOperations.bulk_create_items(
                container, 
                items,
                partition_key_path=partition_key_path
            )
            self.logger.info(f"Bulk created {len(result)} items in {container_name} container")
            return result
        except Exception as e:
            self.logger.error(f"Failed to bulk create items in {container_name}: {e}")
            raise
    
    async def bulk_upsert_items(
        self, 
        container_name: str, 
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Bulk upsert (insert or update) items in specified container.
        
        Args:
            container_name: Name of the container ('conversations', 'users', 'gold')
            items: List of items to upsert
            
        Returns:
            List of successfully upserted items
        """
        try:
            container = self._get_container(container_name)
            
            # Determine partition key path based on container
            if container_name == 'gold':
                partition_key_path = 'pkType,pkFilter'  # Hierarchical partition key
            else:
                partition_key_path = 'partitionKey'  # Single partition key
            
            result = await CosmosBulkOperations.bulk_upsert_items(
                container, 
                items,
                partition_key_path=partition_key_path
            )
            self.logger.info(f"Bulk upserted {len(result)} items in {container_name} container")
            return result
        except Exception as e:
            self.logger.error(f"Failed to bulk upsert items in {container_name}: {e}")
            raise
    
    async def bulk_delete_items(
        self, 
        container_name: str, 
        item_ids: List[tuple[str, str]]
    ) -> int:
        """
        Bulk delete items from specified container.
        
        Args:
            container_name: Name of the container ('conversations', 'users', 'gold')
            item_ids: List of (item_id, partition_key) tuples for single partition key,
                      or List of (item_id, [pk1, pk2, ...]) for hierarchical partition keys
            
        Returns:
            Number of successfully deleted items
        """
        try:
            container = self._get_container(container_name)
            
            # Note: bulk_delete_items receives item_ids with partition key values already,
            # so it doesn't need the partition_key_path parameter
            deleted_count = await CosmosBulkOperations.bulk_delete_items(container, item_ids)
            self.logger.info(f"Bulk deleted {deleted_count} items from {container_name} container")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Failed to bulk delete items from {container_name}: {e}")
            raise
    

# Global service instance
_cosmos_service: Optional[CosmosDBService] = None


def get_cosmos_service() -> CosmosDBService:
    """Get or create Cosmos DB service instance."""
    global _cosmos_service
    if _cosmos_service is None:
        _cosmos_service = CosmosDBService()
    return _cosmos_service
