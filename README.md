# Cricket Athletes Collection Bot

A Telegram bot for collecting, trading, and managing cricket athlete cards. This bot allows users to collect cricket players, build teams, trade with other users, and participate in various game mechanics.

## Features

### Core Features
- **Athlete Collection**: Collect cricket players of different rarities
- **Team Building**: Create and manage teams of cricket athletes
- **Trading System**: Trade athletes with other users
- **Global Market**: Buy and sell athletes on a global marketplace
- **Leaderboards**: Compete with other users on various leaderboards
- **Smash System**: Special collection mechanic for rare athletes
- **Gift System**: Send athletes as gifts to other users
- **Search**: Find specific athletes in your collection
- **Advanced Search**: Search with multiple filters and criteria
- **Wallet System**: Manage in-game currency

### Game Mechanics
- **Drop System**: Regular drops of new athletes to collect
- **Claim System**: Claim new athletes at regular intervals
- **Steal Mechanic**: Attempt to steal athletes from other users
- **Fight System**: Battle other users with your athletes
- **Achievement System**: Complete tasks to earn rewards
- **Redeem System**: Redeem codes for special rewards

### User Experience
- **Multi-language Support**: Bot supports multiple languages
- **Preference Settings**: Customize your bot experience
- **Status Display**: View your collection statistics
- **Help Command**: Get assistance with bot commands

## Installation

### Prerequisites
- Python 3.8+
- MongoDB
- Telegram Bot Token

### Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/Collect-Cricket-Athletes.git
cd Collect-Cricket-Athletes
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
   - Update `Bot/config.py` with your API credentials and settings

4. Start the bot:
```bash
python -m Bot
```

## Commands

### Basic Commands
- `/start` - Start the bot and see welcome message
- `/help` - Get help with bot commands
- `/ping` - Check if the bot is online
- `/mycollection` or `/harem` - View your collection of athletes

### Collection Management
- `/claim` - Claim a new athlete (time-limited)
- `/mclaim` - Claim multiple athletes at once
- `/drop` - View current athlete drops
- `/search` - Search for specific athletes
- `/advsearch` - Advanced search with multiple criteria
- `/check` - Check details of a specific athlete

### Trading and Economy
- `/trade` - Trade athletes with other users
- `/gift` - Gift an athlete to another user
- `/massgift` - Gift multiple athletes at once
- `/store` - Access the in-game store
- `/globalmarket` - Access the global marketplace
- `/manualsell` - Manually sell athletes

### Team Management
- `/team` - Manage your cricket teams
- `/fight` - Battle other users with your team

### User Settings
- `/language` - Change your language preference
- `/preference` - Set your bot preferences
- `/refer` - Get your referral link

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# IPL Card System for Cricket Bot

This system allows you to upload IPL-themed player cards that will only be available during specific date ranges in IST (Indian Standard Time).

## Features

- Upload IPL player cards with specific date ranges
- Cards will only drop during their specified date range
- Special IPL-themed drop messages
- Admin commands to manage and view IPL cards
- User commands to check available IPL cards

## Admin Commands

- `/ipl_list` - View all IPL players in the database with their active status
- Use the Admin Panel to add new IPL players with date ranges

## User Commands

- `/ipl_status` - Check which IPL players are available on the current date
- `/ipl_drop` - Force drop an IPL player that is available on the current date (admin only)

## How to Add IPL Players

1. Access the Admin Panel by sending `⚙ Admin Panel ⚙` to the bot in private
2. Click on "🏏 Add IPL Player"
3. Follow the prompts to upload an image, enter player details, and set the date range
4. The date range should be in YYYY-MM-DD format (e.g., 2024-04-15)
5. Confirm the upload

## How IPL Cards Work

- IPL cards will only be available for drops during their specified date range
- The system uses IST (Indian Standard Time) for date calculations
- There's a 20% chance that a date-restricted IPL card will be dropped during regular drops
- You can use `/ipl_drop` to force drop an IPL card that is available on the current date

## Requirements

Make sure you have all the required dependencies installed:

```
pip install -r requirements.txt
```

## Notes

- The date range is inclusive (both start and end dates are included)
- IPL cards are automatically tagged with the "IPL 2025" event
- You can view all IPL cards using the "📋 View IPL Players" button in the Admin Panel 