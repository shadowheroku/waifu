from datetime import datetime, timedelta
from bson.objectid import ObjectId
from Bot.database import db
from Bot.database.smashdb import update_smashed_image, remove_smash_image
from Bot.database.grabtokendb import decrease_grab_token, add_grab_token
from Bot.database.characterdb import get_character_details
import asyncio
from typing import List, Dict, Any, Optional, Tuple


db.Auctions = db["Auctions"]
db.AuctionHistory = db["AuctionHistory"]
db.AuctionBids = db["AuctionBids"]
db.AuctionAuditLog = db["AuctionAuditLog"]


global_auction_lock = asyncio.Lock()

class AuctionHouse:
    
    async def create_auction(self, 
                            seller_id: int, 
                            player_id: str, 
                            starting_price: int, 
                            duration_hours: int = 24, 
                            min_bid_increment: int = 1000,
                            reserve_price: Optional[int] = None,
                            seller_name: Optional[str] = None) -> Optional[str]:

        async with global_auction_lock:
            # Check if player exists in seller's collection
            user_collection = await db.Collection.find_one({"user_id": seller_id})
            if not user_collection or not any(img["image_id"] == player_id for img in user_collection.get("images", [])):
                return None
            
            # Check if this player is already in an active auction
            existing_auction = await db.Auctions.find_one({
                "player_id": player_id,
                "status": "active"
            })
            
            if existing_auction:
                return None  # Player already in an active auction
                
            # Remove player from seller's collection
            await remove_smash_image(seller_id, player_id, seller_name)
            
            # Calculate end time
            end_time = datetime.utcnow() + timedelta(hours=duration_hours)
            
            # Create auction document
            auction = {
                "seller_id": seller_id,
                "player_id": player_id,
                "starting_price": starting_price,
                "current_price": starting_price,
                "min_bid_increment": min_bid_increment,
                "reserve_price": reserve_price,
                "highest_bidder": None,
                "bids": [],
                "created_at": datetime.utcnow(),
                "ends_at": end_time,
                "status": "active",  # active, completed, cancelled, expired
                "seller_name": seller_name
            }
            
            result = await db.Auctions.insert_one(auction)
            
            # Record in audit log
            await db.AuctionAuditLog.insert_one({
                "action": "create_auction",
                "auction_id": result.inserted_id,
                "player_id": player_id,
                "seller_id": seller_id,
                "timestamp": datetime.utcnow(),
                "details": {
                    "starting_price": starting_price,
                    "duration_hours": duration_hours,
                    "reserve_price": reserve_price
                }
            })
            
            return str(result.inserted_id)
    
    async def place_bid(self, 
                       auction_id: str, 
                       bidder_id: int, 
                       bid_amount: int,
                       bidder_name: Optional[str] = None) -> Dict[str, Any]:

        async with global_auction_lock:
            # Get auction
            auction = await db.Auctions.find_one({"_id": ObjectId(auction_id)})
            if not auction:
                return {"success": False, "message": "Auction not found"}
                
            # Check if auction is active
            if auction["status"] != "active":
                return {"success": False, "message": f"Auction is {auction['status']}"}
                
            # Check if auction has ended
            if datetime.utcnow() > auction["ends_at"]:
                # Mark auction as expired
                await db.Auctions.update_one(
                    {"_id": ObjectId(auction_id)},
                    {"$set": {"status": "expired"}}
                )
                return {"success": False, "message": "Auction has ended"}
                
            # Check if bidder is the seller
            if bidder_id == auction["seller_id"]:
                return {"success": False, "message": "You cannot bid on your own auction"}
                
            # Check if both bidder and seller are admins (prevent token leakage)
            if await self._is_admin(bidder_id) and await self._is_admin(auction["seller_id"]):
                return {"success": False, "message": "Admins cannot bid on other admin auctions to prevent token leakage"}
                
            # Check if bid is high enough
            current_price = auction["current_price"]
            min_increment = auction["min_bid_increment"]
            
            if bid_amount < current_price + min_increment:
                return {
                    "success": False, 
                    "message": f"Bid must be at least {current_price + min_increment} GRABTOKENS"
                }
                
            # Check if bidder has enough funds
            if not await decrease_grab_token(bidder_id, bid_amount, bidder_name):
                return {"success": False, "message": "Insufficient funds"}
                
            # Refund previous highest bidder if exists
            if auction["highest_bidder"]:
                prev_bidder = auction["highest_bidder"]
                prev_amount = auction["current_price"]
                await add_grab_token(prev_bidder, prev_amount)
                
            # Record bid
            bid_record = {
                "bidder_id": bidder_id,
                "bidder_name": bidder_name,
                "amount": bid_amount,
                "time": datetime.utcnow()
            }
            
            # Update auction
            await db.Auctions.update_one(
                {"_id": ObjectId(auction_id)},
                {
                    "$set": {
                        "current_price": bid_amount,
                        "highest_bidder": bidder_id
                    },
                    "$push": {"bids": bid_record}
                }
            )
            
            # Record in audit log
            await db.AuctionAuditLog.insert_one({
                "action": "place_bid",
                "auction_id": ObjectId(auction_id),
                "player_id": auction["player_id"],
                "bidder_id": bidder_id,
                "timestamp": datetime.utcnow(),
                "details": {
                    "bid_amount": bid_amount,
                    "previous_price": current_price,
                    "previous_bidder": auction.get("highest_bidder")
                }
            })
            
            # Check if auction should be extended (anti-sniping)
            # If bid is placed in the last 5 minutes, extend by 5 minutes
            time_left = auction["ends_at"] - datetime.utcnow()
            if time_left < timedelta(minutes=5):
                new_end_time = datetime.utcnow() + timedelta(minutes=5)
                await db.Auctions.update_one(
                    {"_id": ObjectId(auction_id)},
                    {"$set": {"ends_at": new_end_time}}
                )
                
            return {
                "success": True, 
                "message": "Bid placed successfully",
                "new_price": bid_amount
            }
    
    async def cancel_auction(self, auction_id: str, user_id: int) -> Dict[str, Any]:
        """
        Cancel an auction
        
        Args:
            auction_id: ID of the auction
            user_id: User ID of the requester (must be seller or admin)
            
        Returns:
            Dict with status and message
        """
        async with global_auction_lock:
            # Get auction
            auction = await db.Auctions.find_one({"_id": ObjectId(auction_id)})
            if not auction:
                return {"success": False, "message": "Auction not found"}
                
            # Check if user is seller or admin
            if user_id != auction["seller_id"] and not await self._is_admin(user_id):
                return {"success": False, "message": "Unauthorized"}
                
            # Check if auction can be cancelled
            if auction["status"] != "active":
                return {"success": False, "message": f"Cannot cancel {auction['status']} auction"}
                
            # If there are bids, refund the highest bidder
            if auction["highest_bidder"]:
                await add_grab_token(auction["highest_bidder"], auction["current_price"])
                
            # Return player to seller
            await update_smashed_image(auction["seller_id"], auction["player_id"])
            
            # Update auction status
            await db.Auctions.update_one(
                {"_id": ObjectId(auction_id)},
                {"$set": {"status": "cancelled"}}
            )
            
            # Record in audit log
            await db.AuctionAuditLog.insert_one({
                "action": "cancel_auction",
                "auction_id": ObjectId(auction_id),
                "player_id": auction["player_id"],
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "details": {
                    "cancelled_by": "seller" if user_id == auction["seller_id"] else "admin",
                    "had_bids": auction["highest_bidder"] is not None
                }
            })
            
            return {"success": True, "message": "Auction cancelled successfully"}
    
    async def complete_auction(self, auction_id: str) -> Dict[str, Any]:
        """
        Complete an auction (called by scheduler or manually by admin)
        
        Args:
            auction_id: ID of the auction
            
        Returns:
            Dict with status and message
        """
        async with global_auction_lock:
            # Get auction
            auction = await db.Auctions.find_one({"_id": ObjectId(auction_id)})
            if not auction:
                return {"success": False, "message": "Auction not found"}
                
            # Check if auction is active
            if auction["status"] != "active":
                return {"success": False, "message": f"Auction is already {auction['status']}"}
                
            # Check if auction has ended
            if datetime.utcnow() < auction["ends_at"]:
                return {"success": False, "message": "Auction has not ended yet"}
                
            # Check if there's a highest bidder
            if not auction["highest_bidder"]:
                # No bids, return player to seller
                await update_smashed_image(auction["seller_id"], auction["player_id"])
                await db.Auctions.update_one(
                    {"_id": ObjectId(auction_id)},
                    {"$set": {"status": "expired"}}
                )
                
                # Record in auction history
                await db.AuctionHistory.insert_one({
                    "auction_id": ObjectId(auction_id),
                    "player_id": auction["player_id"],
                    "seller_id": auction["seller_id"],
                    "winner_id": None,
                    "starting_price": auction["starting_price"],
                    "final_price": auction["current_price"],
                    "created_at": auction["created_at"],
                    "completed_at": datetime.utcnow(),
                    "status": "expired",
                    "bids_count": len(auction["bids"])
                })
                
                # Record in audit log
                await db.AuctionAuditLog.insert_one({
                    "action": "expire_auction",
                    "auction_id": ObjectId(auction_id),
                    "player_id": auction["player_id"],
                    "timestamp": datetime.utcnow(),
                    "details": {
                        "reason": "no_bids"
                    }
                })
                
                return {"success": True, "message": "Auction expired with no bids"}
                
            # Check if reserve price was met
            if auction["reserve_price"] and auction["current_price"] < auction["reserve_price"]:
                # Reserve not met, return player to seller and refund highest bidder
                await update_smashed_image(auction["seller_id"], auction["player_id"])
                await add_grab_token(auction["highest_bidder"], auction["current_price"])
                await db.Auctions.update_one(
                    {"_id": ObjectId(auction_id)},
                    {"$set": {"status": "reserve_not_met"}}
                )
                
                # Record in auction history
                await db.AuctionHistory.insert_one({
                    "auction_id": ObjectId(auction_id),
                    "player_id": auction["player_id"],
                    "seller_id": auction["seller_id"],
                    "winner_id": None,
                    "starting_price": auction["starting_price"],
                    "final_price": auction["current_price"],
                    "created_at": auction["created_at"],
                    "completed_at": datetime.utcnow(),
                    "status": "reserve_not_met",
                    "bids_count": len(auction["bids"])
                })
                
                # Record in audit log
                await db.AuctionAuditLog.insert_one({
                    "action": "reserve_not_met",
                    "auction_id": ObjectId(auction_id),
                    "player_id": auction["player_id"],
                    "timestamp": datetime.utcnow(),
                    "details": {
                        "reserve_price": auction["reserve_price"],
                        "final_bid": auction["current_price"],
                        "highest_bidder": auction["highest_bidder"]
                    }
                })
                
                return {"success": True, "message": "Auction ended but reserve price not met"}
                
            # Complete the auction
            # Transfer player to highest bidder
            await update_smashed_image(auction["highest_bidder"], auction["player_id"])
            
            # Transfer funds to seller (minus platform fee if implemented)
            await add_grab_token(auction["seller_id"], auction["current_price"])
            
            # Update auction status
            await db.Auctions.update_one(
                {"_id": ObjectId(auction_id)},
                {"$set": {"status": "completed"}}
            )
            
            # Record in auction history
            await db.AuctionHistory.insert_one({
                "auction_id": ObjectId(auction_id),
                "player_id": auction["player_id"],
                "seller_id": auction["seller_id"],
                "winner_id": auction["highest_bidder"],
                "starting_price": auction["starting_price"],
                "final_price": auction["current_price"],
                "created_at": auction["created_at"],
                "completed_at": datetime.utcnow(),
                "status": "completed",
                "bids_count": len(auction["bids"])
            })
            
            # Record in audit log
            await db.AuctionAuditLog.insert_one({
                "action": "complete_auction",
                "auction_id": ObjectId(auction_id),
                "player_id": auction["player_id"],
                "timestamp": datetime.utcnow(),
                "details": {
                    "seller_id": auction["seller_id"],
                    "winner_id": auction["highest_bidder"],
                    "final_price": auction["current_price"],
                    "bids_count": len(auction["bids"])
                }
            })
            
            return {
                "success": True, 
                "message": "Auction completed successfully",
                "winner": auction["highest_bidder"],
                "final_price": auction["current_price"]
            }
    
    async def get_auction(self, auction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get auction details
        
        Args:
            auction_id: ID of the auction
            
        Returns:
            Auction details or None if not found
        """
        auction = await db.Auctions.find_one({"_id": ObjectId(auction_id)})
        if auction:
            # Convert ObjectId to string for serialization
            auction["_id"] = str(auction["_id"])
            
            # Add player details
            player_details = await get_character_details(auction["player_id"])
            if player_details:
                auction["player_details"] = player_details
                
            return auction
        return None
    
    async def get_active_auctions(self, page: int = 1, per_page: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get active auctions with pagination
        
        Args:
            page: Page number
            per_page: Number of auctions per page
            
        Returns:
            Tuple of (auctions list, total count)
        """
        skip = (page - 1) * per_page
        
        # Get active auctions
        cursor = db.Auctions.find({"status": "active"}).sort("ends_at", 1).skip(skip).limit(per_page)
        auctions = await cursor.to_list(length=per_page)
        
        # Convert ObjectId to string for each auction
        for auction in auctions:
            auction["_id"] = str(auction["_id"])
            
            # Add player details
            player_details = await get_character_details(auction["player_id"])
            if player_details:
                auction["player_details"] = player_details
        
        # Get total count
        total = await db.Auctions.count_documents({"status": "active"})
        
        return auctions, total
    
    async def get_user_auctions(self, user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get auctions created by a user
        
        Args:
            user_id: User ID
            status: Optional filter by status
            
        Returns:
            List of auctions
        """
        query = {"seller_id": user_id}
        if status:
            query["status"] = status
            
        cursor = db.Auctions.find(query).sort("created_at", -1)
        auctions = await cursor.to_list(length=None)
        
        # Convert ObjectId to string for each auction
        for auction in auctions:
            auction["_id"] = str(auction["_id"])
            
            # Add player details
            player_details = await get_character_details(auction["player_id"])
            if player_details:
                auction["player_details"] = player_details
        
        return auctions
    
    async def get_user_bids(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get auctions where a user has placed bids
        
        Args:
            user_id: User ID
            
        Returns:
            List of auctions
        """
        # Find auctions where user has bid
        cursor = db.Auctions.find({"bids.bidder_id": user_id}).sort("ends_at", 1)
        auctions = await cursor.to_list(length=None)
        
        # Convert ObjectId to string for each auction
        for auction in auctions:
            auction["_id"] = str(auction["_id"])
            
            # Add player details
            player_details = await get_character_details(auction["player_id"])
            if player_details:
                auction["player_details"] = player_details
                
            # Filter bids to only show this user's bids
            user_bids = [bid for bid in auction["bids"] if bid["bidder_id"] == user_id]
            auction["user_bids"] = user_bids
        
        return auctions
    
    async def search_auctions(self, 
                             player_id: Optional[str] = None, 
                             max_price: Optional[int] = None,
                             seller_id: Optional[int] = None,
                             rarity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for auctions with filters
        
        Args:
            player_id: Optional player ID filter
            max_price: Optional maximum current price filter
            seller_id: Optional seller ID filter
            rarity: Optional rarity filter (requires fetching player details)
            
        Returns:
            List of matching auctions
        """
        query = {"status": "active"}
        
        if player_id:
            query["player_id"] = player_id
            
        if max_price:
            query["current_price"] = {"$lte": max_price}
            
        if seller_id:
            query["seller_id"] = seller_id
            
        # Fetch auctions
        cursor = db.Auctions.find(query).sort("ends_at", 1)
        auctions = await cursor.to_list(length=None)
        
        # If rarity filter is applied, we need to filter after fetching player details
        if rarity:
            filtered_auctions = []
            for auction in auctions:
                player_details = await get_character_details(auction["player_id"])
                if player_details and player_details.get("rarity") == rarity:
                    auction["_id"] = str(auction["_id"])
                    auction["player_details"] = player_details
                    filtered_auctions.append(auction)
            return filtered_auctions
        
        # Convert ObjectId to string for each auction
        for auction in auctions:
            auction["_id"] = str(auction["_id"])
            
            # Add player details
            player_details = await get_character_details(auction["player_id"])
            if player_details:
                auction["player_details"] = player_details
        
        return auctions
    
    async def process_expired_auctions(self) -> int:
        """
        Process all expired auctions
        
        Returns:
            Number of auctions processed
        """
        # Find expired but still active auctions
        query = {
            "status": "active",
            "ends_at": {"$lt": datetime.utcnow()}
        }
        
        cursor = db.Auctions.find(query)
        expired_auctions = await cursor.to_list(length=None)
        
        count = 0
        for auction in expired_auctions:
            auction_id = str(auction["_id"])
            result = await self.complete_auction(auction_id)
            if result["success"]:
                count += 1
        
        return count
    
    async def get_auction_history(self, player_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get auction history for price tracking
        
        Args:
            player_id: Optional player ID to filter history
            
        Returns:
            List of completed auctions
        """
        query = {"status": "completed"}
        if player_id:
            query["player_id"] = player_id
            
        # Get completed auctions sorted by completion time
        cursor = db.Auctions.find(query).sort("ends_at", -1)
        auctions = await cursor.to_list(length=None)
        
        # Convert ObjectId to string for each auction
        for auction in auctions:
            auction["_id"] = str(auction["_id"])
            
            # Add player details
            player_details = await get_character_details(auction["player_id"])
            if player_details:
                auction["player_details"] = player_details
        
        return auctions
    
    async def _is_admin(self, user_id: int) -> bool:
        """
        Check if a user is an admin
        
        Args:
            user_id: User ID
            
        Returns:
            True if user is admin, False otherwise
        """
        from Bot.config import OWNERS
        from Bot.database.privacydb import is_user_sudo, is_user_og
        
        if user_id in OWNERS or await is_user_sudo(user_id) or await is_user_og(user_id):
            return True
        return False

# Create singleton instance
auction_house = AuctionHouse()

