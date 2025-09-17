import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import tweepy
from vertexai.generative_models import GenerativeModel
import vertexai
from dataclasses import dataclass
import sqlite3
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trader_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradeData:
    proxy_wallet: str
    side: str
    asset: str
    condition_id: str
    size: float
    price: float
    timestamp: int
    title: str
    slug: str
    icon: str
    event_slug: str
    outcome: str
    outcome_index: int
    name: str
    pseudonym: str
    bio: str
    profile_image: str
    transaction_hash: str

@dataclass
class EventData:
    id: str
    slug: str
    title: str
    description: str
    image: str
    markets: List[dict]
    volume: float
    liquidity: float
    start_date: str
    end_date: str

class PolymarketTraderAPI:
    """Handles Polymarket API interactions for trader data"""
    
    BASE_URL1 = "https://data-api.polymarket.com/trades"
    BASE_URL2 = "https://gamma-api.polymarket.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PolymarketTraderTracker/1.0'
        })
    
    def get_user_trades(self, user_address: str, limit: int = 10, taker_only: bool = True) -> List[TradeData]:
        """Get trades for a specific user"""
        try:
            url = f"{self.BASE_URL1}/"
            params = {
                'limit': limit,
                'takerOnly': str(taker_only).lower(),
                'user': user_address
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            trades = []
            
            for trade_item in data:
                trade = TradeData(
                    proxy_wallet=trade_item.get('proxyWallet', ''),
                    side=trade_item.get('side', ''),
                    asset=trade_item.get('asset', ''),
                    condition_id=trade_item.get('conditionId', ''),
                    size=float(trade_item.get('size', 0)),
                    price=float(trade_item.get('price', 0)),
                    timestamp=int(trade_item.get('timestamp', 0)),
                    title=trade_item.get('title', ''),
                    slug=trade_item.get('slug', ''),
                    icon=trade_item.get('icon', ''),
                    event_slug=trade_item.get('eventSlug', ''),
                    outcome=trade_item.get('outcome', ''),
                    outcome_index=int(trade_item.get('outcomeIndex', 0)),
                    name=trade_item.get('name', ''),
                    pseudonym=trade_item.get('pseudonym', ''),
                    bio=trade_item.get('bio', ''),
                    profile_image=trade_item.get('profileImage', ''),
                    transaction_hash=trade_item.get('transactionHash', '')
                )
                trades.append(trade)
            
            logger.info(f"📊 Retrieved {len(trades)} trades for user {user_address[:10]}...")
            return trades
            
        except Exception as e:
            logger.error(f"❌ Error fetching trades for user {user_address}: {e}")
            return []
    
    def get_event_by_slug(self, slug: str) -> Optional[EventData]:
        """Get event details by slug"""
        try:
            url = f"{self.BASE_URL2}/events/slug/{slug}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            event = EventData(
                id=data.get('id', ''),
                slug=data.get('slug', ''),
                title=data.get('title', ''),
                description=data.get('description', ''),
                image=data.get('image', ''),
                markets=data.get('markets', []),
                volume=float(data.get('volume', 0)),
                liquidity=float(data.get('liquidity', 0)),
                start_date=data.get('startDate', ''),
                end_date=data.get('endDate', '')
            )
            
            logger.info(f"📈 Retrieved event data for slug: {slug}")
            return event
            
        except Exception as e:
            logger.error(f"❌ Error fetching event for slug {slug}: {e}")
            return None

class TraderAnalyzer:
    """Handles AI analysis using Vertex AI Gemini for trader tweets"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize Vertex AI"""
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.5-pro")
        
    async def generate_trade_tweet(self, trade: TradeData, event: EventData) -> Optional[str]:
        """Generate engaging tweet about a trader's move"""
        try:
            prompt = self._create_trade_tweet_prompt(trade, event)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.model.generate_content, prompt
            )
            
            tweet_text = response.text.strip()
            
            # Ensure tweet is within Twitter's character limit
            if len(tweet_text) > 180:  # Leave more room for URL and call to action
                tweet_text = tweet_text[:180] + "..."
            
            # Add subtle call to action based on trade size
            trade_value = trade.size * trade.price
            if trade_value >= 25000:
                cta = "👀 Watch this space"
            elif trade_value >= 10000:
                cta = "📊 Market moving"
            else:
                cta = "🎯 Trade alert"
            
            # Add the Polymarket URL with enhanced formatting
            polymarket_url = f"https://polymarket.com/event/{event.slug}"
            final_tweet = f"{tweet_text}\n\n{cta} 🔗 {polymarket_url}"
            
            logger.info(f"🎯 Generated FOMO tweet for trade by {trade.name or trade.pseudonym}")
            return final_tweet
            
        except Exception as e:
            logger.error(f"❌ Error generating tweet for trade: {e}")
            return None
    
    def _create_trade_tweet_prompt(self, trade: TradeData, event: EventData) -> str:
        """Create prompt for generating trade tweet"""
        
        # Calculate trade value
        trade_value = trade.size * trade.price
        
        # Get trader name (prefer name over pseudonym)
        trader_name = trade.name if trade.name else trade.pseudonym
        if not trader_name:
            trader_name = f"Trader {trade.proxy_wallet[:8]}..."
        
        # Get market probabilities if available
        market_info = ""
        if event.markets:
            for market in event.markets:
                if market.get('outcomes') and market.get('outcomePrices'):
                    outcomes = market['outcomes']
                    prices = market['outcomePrices']
                    if len(outcomes) == len(prices):
                        probs = [f"{outcomes[i]}: {float(prices[i])*100:.1f}%" for i in range(len(outcomes))]
                        market_info = f"Current odds: {', '.join(probs)}"
                        break
        
        # Determine trade size category for better language
        if trade_value >= 50000:
            size_descriptor = "MASSIVE"
        elif trade_value >= 25000:
            size_descriptor = "HUGE"
        elif trade_value >= 10000:
            size_descriptor = "BIG"
        else:
            size_descriptor = "NOTABLE"
        
        return f"""
        You are a financial news reporter creating viral Twitter content about prediction market trades that creates FOMO while staying professional.

        TRADE DETAILS:
        - Trader: {trader_name}
        - Action: {trade.side} (bought/sold)
        - Market: {trade.title}
        - Outcome: {trade.outcome}
        - Size: ${trade.size:,.2f}
        - Price: {trade.price:.3f} ({trade.price*100:.1f}%)
        - Trade Value: ${trade_value:,.2f}
        - Size Category: {size_descriptor}
        - Time: {datetime.fromtimestamp(trade.timestamp).strftime('%Y-%m-%d %H:%M')}

        EVENT DETAILS:
        - Title: {event.title}
        - Description: {event.description}
        - Volume: ${event.volume:,.0f}
        {market_info}

        Create a FOMO-inducing tweet following these enhanced examples:

        "🚨 WHALE ALERT: Smart money moving! Trader 'AlphaBettor' just loaded $50K on 'Bitcoin $100K by 2024' at 65% odds. Market heating up!"

        "BREAKING: Top trader 'CryptoWhale92' sees something we don't - drops $25K on 'Trump 2024' while odds still at 45%. Following the money..."

        "🔥 INSIDER MOVE: Wallet 0x56687bf4... bets $75K that 'AI replaces 50% jobs by 2030' at just 23% odds. They know something?"

        "JUST IN: Smart money flowing! Veteran trader 'PolyKing' loads $40K on 'Recession by Q2' at 30% odds. Market shift incoming?"

        ENHANCED RULES FOR FOMO:
        1. Start with "🚨 WHALE ALERT:", "BREAKING:", "🔥 INSIDER MOVE:", or "JUST IN:"
        2. ALWAYS mention the actual trader name/pseudonym or wallet address (first 10 chars + ...) for legitimacy
        3. Use phrases like "Smart money moving", "They know something?", "Following the money", "Market heating up"
        4. Include the trade size and outcome with urgency
        5. Add momentum indicators: "Market shift incoming?", "Odds moving fast", "Volume surging"
        6. Use psychological triggers: "sees something we don't", "while odds still at", "before it's too late"
        7. Keep under 200 characters for URL space
        8. Sound like insider financial intelligence
        9. Use terms: "whale", "smart money", "veteran trader", "insider move", "loading up"
        10. Add subtle urgency without being pushy
        11. Create curiosity: "They know something?", "What do they see?"
        12. NO hashtags, minimal emojis (🚨🔥 only for alerts)
        13. MUST include the trader identifier ({trader_name}) in the tweet for credibility
        14. If trader has a name/pseudonym, use it in quotes. If only wallet, use "Wallet 0x..." format

        Write ONLY the tweet text:
        """

class TwitterBot:
    """Handles Twitter API interactions"""
    
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        """Initialize Twitter API v2 client"""
        self.client = tweepy.Client(
            bearer_token=None,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )
    
    async def post_tweet(self, content: str) -> bool:
        """Post tweet to Twitter"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.create_tweet(text=content)
            )
            if response.data:
                logger.info(f"🚀 Tweet posted successfully | Tweet ID: {response.data['id']}")
                return True
            else:
                logger.error("❌ Failed to post tweet - no response data")
                return False
        except Exception as e:
            logger.error(f"❌ Error posting tweet: {e}")
            return False

class TradeDatabase:
    """Handles local database for tracking posted trades"""
    
    def __init__(self, db_path: str = "trader_tracker.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS posted_trades (
                    transaction_hash TEXT PRIMARY KEY,
                    trader_address TEXT,
                    trade_size REAL,
                    trade_timestamp INTEGER,
                    slug TEXT,
                    posted_at TIMESTAMP,
                    tweet_content_hash TEXT
                )
            """)
            conn.commit()
    
    def is_trade_posted(self, trade: TradeData) -> bool:
        """Check if trade was already posted"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM posted_trades WHERE transaction_hash = ?",
                (trade.transaction_hash,)
            )
            return cursor.fetchone() is not None
    
    def mark_trade_as_posted(self, trade: TradeData, tweet_content: str):
        """Mark trade as posted"""
        content_hash = hashlib.md5(tweet_content.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO posted_trades 
                (transaction_hash, trader_address, trade_size, trade_timestamp, slug, posted_at, tweet_content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.transaction_hash,
                trade.proxy_wallet,
                trade.size,
                trade.timestamp,
                trade.slug,
                datetime.now(),
                content_hash
            ))
            conn.commit()
    
    def cleanup_old_records(self, days: int = 7):
        """Clean up old records to prevent database bloat"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM posted_trades WHERE posted_at < ?", (cutoff_date,))
            conn.commit()

class TraderTracker:
    """Main class for tracking top traders and generating tweets"""
    
    def __init__(self, config: Dict):
        self.api = PolymarketTraderAPI()
        self.analyzer = TraderAnalyzer(
            project_id=config['vertex_ai']['project_id'],
            location=config['vertex_ai'].get('location', 'us-central1')
        )
        self.twitter = TwitterBot(
            api_key=config['twitter']['api_key'],
            api_secret=config['twitter']['api_secret'],
            access_token=config['twitter']['access_token'],
            access_token_secret=config['twitter']['access_token_secret']
        )
        self.database = TradeDatabase()
        self.config = config
        
        # List of top trader wallet addresses
        self.top_traders = [
            "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
            "0x2635b7fb040d817f4c7e7f45fdd116bf476d5408", 
            "0xd2c5d404493dc772fde0990a61e64ef1120079a0",
            "0xb68a63d94676c8630eb3471d82d3d47b7533c568",
            "0x2adf85be1f25a77ca407cf031bd00d735c05d89c",
            "0x3a6238d6a4d545e27dae2af2d04475efce8b1106",
            "0x83b9f9e2d28ab875b9c9f73cdd5535c4c8926124",
            "0xa49becb692927d455924583b5e3e5788246f4c40",
            "0x6f06f9436fbc17cdd396e5943a14865065c5515a", 
            "0xa49becb692927d455924583b5e3e5788246f4c40",
            "0x14964aefa2cd7caff7878b3820a690a03c5aa429",
            "0xd42f6a1634a3707e27cbae14ca966068e5d1047d", 
            
            # Add more top trader addresses here
        ]
    
    def _is_trade_recent(self, timestamp: int, max_hours: int = 12) -> bool:
        """Check if trade is within the specified hours"""
        trade_time = datetime.fromtimestamp(timestamp)
        current_time = datetime.now()
        time_diff = current_time - trade_time
        return time_diff.total_seconds() <= (max_hours * 3600)
    
    def _find_best_trade(self, trades: List[TradeData]) -> Optional[TradeData]:
        """Find the best trade based on criteria: BUY side, recent (12h), largest size"""
        # Filter for BUY trades only
        buy_trades = [trade for trade in trades if trade.side == "BUY"]
        
        if not buy_trades:
            logger.info("❌ No BUY trades found")
            return None
        
        # Filter for recent trades (within 12 hours)
        recent_trades = [trade for trade in buy_trades if self._is_trade_recent(trade.timestamp, 12)]
        
        if not recent_trades:
            logger.info("❌ No recent BUY trades found (within 12 hours)")
            return None
        
        # Find the trade with the largest size
        best_trade = max(recent_trades, key=lambda t: t.size)
        
        logger.info(f"✅ Found best trade: ${best_trade.size:,.2f} by {best_trade.name or best_trade.pseudonym}")
        return best_trade
    
    async def run_cycle(self):
        """Run one complete cycle of trader tracking"""
        logger.info("🔥 Starting trader tracking cycle")
        
        try:
            # Randomly select a trader from the list
            selected_trader = random.choice(self.top_traders)
            logger.info(f"🎯 Selected trader: {selected_trader}")
            
            # Get trades for the selected trader
            trades = self.api.get_user_trades(selected_trader, limit=10, taker_only=True)
            
            if not trades:
                logger.warning(f"⚠️ No trades found for trader {selected_trader}")
                return
            
            # Find the best trade based on criteria
            best_trade = self._find_best_trade(trades)
            
            if not best_trade:
                logger.info("❌ No suitable trade found, restarting process...")
                # Recursively try again with a different trader
                await self.run_cycle()
                return
            
            # Check if this trade has already been posted
            if self.database.is_trade_posted(best_trade):
                logger.info(f"🔄 Trade {best_trade.transaction_hash[:10]}... already posted, finding another...")
                # Recursively try again with a different trader
                await self.run_cycle()
                return
            
            # Get event details using the slug
            event = self.api.get_event_by_slug(best_trade.slug)
            
            if not event:
                logger.error(f"❌ Could not fetch event details for slug: {best_trade.slug}")
                logger.info("🔄 Restarting cycle to find another trader...")
                # Recursively try again with a different trader
                await self.run_cycle()
                return
            
            # Generate tweet using AI
            tweet_content = await self.analyzer.generate_trade_tweet(best_trade, event)
            
            if not tweet_content:
                logger.error("❌ Failed to generate tweet content")
                return
            
            print("Generated tweet:", tweet_content)
            
            # Post to Twitter
            if await self.twitter.post_tweet(tweet_content):
                # Mark trade as posted in database
                self.database.mark_trade_as_posted(best_trade, tweet_content)
                logger.info("✅ Successfully posted trader tweet and marked as posted")
            else:
                logger.error("❌ Failed to post tweet")
                
        except Exception as e:
            logger.error(f"❌ Error in trader tracking cycle: {e}")
    
    async def run_forever(self):
        """Run the trader tracker continuously"""
        logger.info("🌟 Trader Tracker v1.0 activated - Monitoring whale movements")
        
        while True:
            try:
                await self.run_cycle()
                
                # Clean up old database records occasionally
                if random.random() < 0.1:  # 10% chance each cycle
                    self.database.cleanup_old_records()
                    logger.info("🧹 Database cleanup completed - old records removed")
                
                # Wait for random interval (30 minutes to 2 hours)
                wait_time = random.randint(1800, 7200)  # 30 min to 2 hours
                logger.info(f"⏰ Waiting {wait_time/3600:.1f} hours before next trader scan")
                await asyncio.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info("🛑 Trader tracker terminated by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in main loop: {e}")
                # Wait 10 minutes before retrying
                logger.info("🔄 Restarting in 10 minutes...")
                await asyncio.sleep(3600)

def load_config() -> Dict:
    """Load configuration"""
    return {
        'vertex_ai': {
            'project_id': 'amw-dna-coe-working-ds-dev',  # Replace with your GCP project ID
            'location': 'us-central1'
        },
        'twitter': {
            'api_key': '0lEFwtuZoW9yoLXVQS1pKOov3',
            'api_secret': 'V4V2S6FqPRcuEFw0PjnurYbVTulasnkME7XK2B55cKXwEYZ9Yo',
            'access_token': "1963945338957639680-hXW0qse3llvQmJjgGAhwrldRSuHzEC",
            'access_token_secret': "UpFVFzc2IN3bitor8cLYWy5mNDVNL8TyKbikDtPLHUNQ4"
        }
    }

async def main():
    """Main entry point"""
    config = load_config()
    tracker = TraderTracker(config)
    
    # Test single cycle
    await tracker.run_cycle()
    
    # Run continuously
    # await tracker.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
