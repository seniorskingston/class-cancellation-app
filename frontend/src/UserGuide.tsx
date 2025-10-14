import React from 'react';

interface UserGuideProps {
  onClose: () => void;
}

const UserGuide: React.FC<UserGuideProps> = ({ onClose }) => {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '90vh', overflow: 'auto' }}>
        <div className="user-guide-content">
          <h2 style={{ color: '#0072ce', textAlign: 'center' }}>📖 Program Schedule Update App – User Guide</h2>

          <h3>1. Getting Started & Installation</h3>
          
          <h4>Accessing the App</h4>
          <ul>
            <li>Open your web browser and go to the app URL:</li>
            <li>🔗 <a href="https://class-cancellation-frontend.onrender.com/" target="_blank" rel="noopener noreferrer" style={{ color: '#0072ce', fontWeight: 'bold' }}>https://class-cancellation-frontend.onrender.com/</a></li>
            <li>The app works on all devices — desktop, tablet, and mobile.</li>
          </ul>

          <h4>Installing as a Mobile App</h4>
          <ul>
            <li><strong>iPhone/iPad (Safari):</strong> Tap 📲 Save App → Tap the Share button (□↑) at the bottom of Safari → Select Add to Home Screen.</li>
            <li><strong>iPhone/iPad (Chrome):</strong> Tap the Share button in the top address bar → Select Add to Home Screen.</li>
            <li><strong>Android (Chrome):</strong> Chrome may prompt automatically, or use the browser menu → Add to Home Screen.</li>
            <li><strong>App Name:</strong> Defaults to "Program" when installed.</li>
            <li><strong>Benefits:</strong> Opens like a native app, provides faster access, and supports offline use.</li>
          </ul>

          <h3>2. Loading Data</h3>
          <ul>
            <li>When you open the app, allow a few moments for data to load.</li>
            <li>If the app was left open previously, refresh the page for the latest updates.</li>
            <li>Data refreshes automatically every 5 minutes.</li>
          </ul>

          <h3>3. Searching for a Program</h3>
          <p>You can search by:</p>
          <ul>
            <li><strong>Program Name</strong></li>
            <li><strong>Program ID</strong></li>
            <li><strong>Day & Location</strong></li>
          </ul>

          <h3>4. Understanding Program Statuses</h3>
          <ul>
            <li><strong>Active</strong> – The program is currently running (default view)</li>
            <li><strong>Cancelled</strong> – The program has been fully cancelled</li>
            <li><strong>Additions</strong> – New programs added after the session began (displayed as Active)</li>
          </ul>
          <p>💡 <strong>Tip:</strong> Use the Active filter to see all current programs.</p>

          <h3>5. Using the View Filter (Dropdown)</h3>
          <ul>
            <li><strong>Show Class Cancellations:</strong> Displays only programs with class cancellations.</li>
            <li><strong>Show All Programs:</strong> Displays all programs, including Active, Cancelled, and Additions.</li>
          </ul>
          <p>💡 <strong>Tip:</strong> Select your preferred option from the dropdown to switch views — data updates instantly.</p>

          <h3>6. Filtering Options (Desktop View)</h3>
          <p>Filter programs by:</p>
          <ul>
            <li><strong>Program Name</strong></li>
            <li><strong>Program ID</strong></li>
            <li><strong>Day</strong></li>
            <li><strong>Location</strong></li>
            <li><strong>Program Status</strong> (Active, Cancelled, Additions)</li>
          </ul>
          <p>💡 <strong>Tip:</strong> When using the mobile version, temporarily switch to Desktop View to search for a program, then return to Mobile View.</p>

          <h3>7. Favorites Feature (Star Pinning)</h3>
          <ul>
            <li><strong>Click the star (★/☆)</strong> to pin a program to the top.</li>
            <li><strong>Favorites are saved</strong> — even after closing the app.</li>
            <li><strong>Each device keeps its own favorites.</strong></li>
            <li><strong>Visual indicator:</strong> Filled star (★): Favorited | Empty star (☆): Not favorited</li>
            <li><strong>Available in both desktop and mobile views.</strong></li>
          </ul>

          <h3>8. Understanding Data Columns</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Column</th>
                <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Star</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Pin program to top (persists across sessions)</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Day</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Day of the week</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program or class name</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program ID</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Unique identifier with message icon (✉️)</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Date Range</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Start and end dates</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Time</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Scheduled time</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Location</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Venue of the program</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Class Room</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Specific room or facility</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Instructor</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Assigned instructor</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Program Status</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Active / Cancelled / Additions</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Class Cancellation</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Specific cancelled dates</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Additional Information</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Notes or details</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Refund</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Yes/No (based on classes completed)</td></tr>
            </tbody>
          </table>

          <h3>9. Mobile View Features</h3>
          <ul>
            <li><strong>Card Layout:</strong> Programs displayed as easy-to-read cards</li>
            <li><strong>Favorites Support:</strong> Star programs to pin them to the top</li>
            <li><strong>Class Cancellations View:</strong> Focuses on cancelled classes</li>
            <li><strong>Touch-Friendly:</strong> Large buttons and easy navigation</li>
            <li><strong>Header Buttons:</strong> 🖥️ Desktop View | 🔄 Refresh | 📲 Save App</li>
            <li><strong>Search:</strong> Search by program name or ID</li>
            <li><strong>PWA Installation:</strong> Can be installed as a native mobile app</li>
          </ul>
          <p>💡 <strong>Tip:</strong> When using the mobile version, switch to Desktop View to search for your preferred program, then return to Mobile View.</p>

          <h3>10. Messaging Feature</h3>
          <ul>
            <li><strong>Message Icon (✉️):</strong> Click to send a message about a specific program.</li>
            <li><strong>Available on:</strong> Both mobile and desktop views.</li>
            <li><strong>How to Use:</strong> Click ✉️ → Type your message → Click Send Message.</li>
            <li><strong>Tooltip:</strong> Hover over ✉️ to see "Send a message regarding this program."</li>
            <li><strong>Each message automatically includes</strong> the program name, ID, and instructor details.</li>
          </ul>

          <h3>11. Event Schedule & Calendar</h3>
          <ul>
            <li><strong>Click the Event Schedule banner</strong> in the header to view upcoming events.</li>
            <li><strong>Navigate by month</strong> to see all scheduled events.</li>
            <li><strong>Click any event</strong> for full details.</li>
            <li><strong>Select "Program"</strong> to return to the main program list.</li>
          </ul>

          <h3>12. QR Code Sharing</h3>
          <ul>
            <li><strong>Desktop:</strong> Click the floating 📱 QR Code button on the right.</li>
            <li><strong>Mobile:</strong> Tap 👥 Share in the header.</li>
            <li><strong>Others can scan the QR code</strong> to access the app instantly.</li>
          </ul>

          <h3>13. Refund Rules</h3>
          <ul>
            <li><strong>Yes:</strong> Refund allowed if fewer than 3 classes are completed.</li>
            <li><strong>No:</strong> Refund not allowed if 3 or more classes are completed.</li>
          </ul>

          <h3>14. Tips & Best Practices</h3>
          <ul>
            <li><strong>Use Favorites (⭐)</strong> to keep important programs at the top.</li>
            <li><strong>Install the app on mobile</strong> for faster access to class cancellations.</li>
            <li><strong>The app automatically adjusts</strong> its layout for your device.</li>
            <li><strong>Use Messaging</strong> to communicate directly about specific programs.</li>
            <li><strong>Share the QR Code</strong> to help others access the app easily.</li>
            <li><strong>Refresh regularly</strong> for the latest updates (auto-refreshes every 5 minutes).</li>
            <li><strong>Check the Event Schedule</strong> for upcoming activities.</li>
            <li>All times are displayed in <strong>Kingston, Ontario (EST)</strong>.</li>
          </ul>

          <h3>15. Troubleshooting</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left', width: '30%' }}>Issue</th>
                <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Solution</th>
              </tr>
            </thead>
            <tbody>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Data not loading</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Refresh the page or use the 🔄 Refresh button</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Favorites missing</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Ensure you're using the same device/browser</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Mobile display issues</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Use the 🖥️ Desktop button to switch views</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Installation problems</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Tap 📲 Save App and follow on-screen steps</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Search not working</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Search by Program Name or Program ID only</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Message not sending</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Check your internet connection and retry</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>QR not showing</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Use 📱 (desktop) or 👥 Share (mobile)</td></tr>
              <tr><td style={{ border: '1px solid #ddd', padding: '8px' }}>Calendar not loading</td><td style={{ border: '1px solid #ddd', padding: '8px' }}>Click Back to Main View and try again</td></tr>
            </tbody>
          </table>

          <h3>16. Support</h3>
          <p>For technical issues or questions, please contact <strong>Seniors Association Administration</strong>.</p>
        </div>
        
        <div className="modal-actions" style={{ textAlign: 'center', padding: '20px' }}>
          <button 
            onClick={onClose} 
            style={{ 
              background: '#0072ce', 
              color: 'white', 
              padding: '12px 30px', 
              border: 'none', 
              borderRadius: '6px', 
              fontSize: '16px', 
              fontWeight: 'bold', 
              cursor: 'pointer' 
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserGuide;

