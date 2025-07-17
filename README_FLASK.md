# Chewy Pet Experience - Flask Web App

A beautiful, responsive Flask web application that mimics a mobile phone display to showcase personalized pet experiences. This app provides a slide-based interface to display AI-generated pet letters, personality badges, and portraits.

## Features

### 🎨 Mobile-First Design
- Realistic phone frame with notch and home indicator
- Responsive design that works on all devices
- Smooth animations and transitions
- Beautiful gradient backgrounds and modern UI

### 📱 Slide-Based Interface
- **Slide 0**: Welcome screen with customer ID input
- **Slide 1**: AI-generated pet letter to human
- **Slide 2**: Personality badge with description
- **Slide 3**: AI-generated pet portrait

### 🎯 Interactive Features
- Touch/swipe navigation between slides
- Keyboard navigation (arrow keys, space bar)
- Smooth slide transitions
- Loading states and error handling
- Responsive navigation dots

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the App**
   - Open your browser and go to `http://localhost:5000`
   - The app will display a mobile phone interface

## Usage

### Landing Page
- Enter a customer ID (e.g., `1154095`)
- Click "Let's Go!" to start the experience
- The app will load personalized data for that customer

### Navigation
- **Touch/Swipe**: Swipe left/right to navigate between slides
- **Navigation Dots**: Click the dots at the top to jump to specific slides
- **Arrow Buttons**: Use the arrow buttons at the bottom
- **Keyboard**: Use arrow keys or space bar to navigate

### Available Customer IDs
The app includes data for the following customer IDs:
- `1154095` (Sue Ling & Sugar - Cats)
- `1183376`
- `1317924`
- `2209529`
- `4093877`
- `4760852`
- `4886040`
- `5025337`
- `5038`
- `5812`
- `6084516`
- `6205413`
- `7653`

## Project Structure

```
chewy-playback/
├── app.py                          # Main Flask application
├── templates/                      # HTML templates
│   ├── base.html                   # Base template with phone frame
│   ├── index.html                  # Landing page
│   ├── experience.html             # Main experience page
│   └── error.html                  # Error page
├── static/                         # Static assets
│   ├── css/
│   │   └── style.css              # Main stylesheet
│   └── js/
│       └── main.js                # JavaScript functionality
├── Final_Pipeline/Output/          # Customer data directory
│   └── [customer_id]/             # Individual customer folders
│       ├── enriched_pet_profile.json
│       ├── personality_badge.json
│       ├── pet_letters.txt
│       └── images/
│           └── collective_pet_portrait.png
├── personalityzipped/              # Badge images
│   ├── badge_diva copy.png
│   ├── badge_cuddler copy.png
│   └── ...
└── requirements.txt                # Python dependencies
```

## API Endpoints

- `GET /` - Landing page
- `GET /experience/<customer_id>` - Main experience page
- `GET /api/customer/<customer_id>` - JSON API for customer data
- `GET /static/customer_images/<customer_id>/<filename>` - Serve customer images
- `GET /static/badges/<filename>` - Serve badge images

## Design Features

### 🎨 Visual Design
- **Phone Frame**: Realistic iPhone-style frame with rounded corners
- **Gradients**: Beautiful gradient backgrounds for each slide
- **Glass Morphism**: Frosted glass effects on cards and containers
- **Animations**: Smooth transitions and hover effects
- **Typography**: Modern fonts (Inter, Fredoka) with proper hierarchy

### 📱 Mobile Experience
- **Touch-Friendly**: Large touch targets and swipe gestures
- **Responsive**: Adapts to different screen sizes
- **Performance**: Optimized animations and smooth scrolling
- **Accessibility**: Keyboard navigation and screen reader support

### 🎯 User Experience
- **Intuitive Navigation**: Clear visual cues and smooth transitions
- **Loading States**: Visual feedback during data loading
- **Error Handling**: Graceful fallbacks for missing data
- **Progressive Enhancement**: Works without JavaScript

## Customization

### Adding New Customers
1. Create a new folder in `Final_Pipeline/Output/[customer_id]/`
2. Add the required files:
   - `enriched_pet_profile.json`
   - `personality_badge.json`
   - `pet_letters.txt`
   - `images/collective_pet_portrait.png`

### Styling
- Modify `static/css/style.css` to change colors, fonts, and layout
- Update gradient backgrounds in the CSS variables
- Customize animations and transitions

### Badge Images
- Add new badge images to `personalityzipped/` folder
- Update the badge mapping in `app.py` if needed

## Browser Support

- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ⚠️ Internet Explorer (limited support)

## Performance

- **Lightweight**: No heavy frameworks, just vanilla HTML/CSS/JS
- **Fast Loading**: Optimized assets and minimal dependencies
- **Smooth Animations**: Hardware-accelerated CSS transitions
- **Responsive Images**: Proper sizing and lazy loading

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development
python app.py
```

### Debug Mode
The app runs with debug mode enabled by default for development.

### File Watching
For development, you can use tools like `flask run` with auto-reload:
```bash
flask run --debug
```

## Deployment

### Production Setup
1. Set `FLASK_ENV=production`
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Environment Variables
- `FLASK_ENV`: Set to 'production' for production deployment
- `FLASK_DEBUG`: Set to 'False' in production

## Troubleshooting

### Common Issues

1. **Images not loading**
   - Check file paths in `Final_Pipeline/Output/`
   - Verify badge images exist in `personalityzipped/`

2. **Customer data not found**
   - Ensure customer ID exists in `Final_Pipeline/Output/`
   - Check JSON file formats are valid

3. **Styling issues**
   - Clear browser cache
   - Check CSS file is being served correctly

### Debug Mode
Enable debug mode to see detailed error messages:
```python
app.run(debug=True)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Chewy Pet Experience pipeline.

---

**Enjoy exploring your pet's personalized experience! 🐾** 