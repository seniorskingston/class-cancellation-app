import React, { useState, useEffect } from 'react';
import './EventEditor.css';

interface Event {
  id?: string;
  title: string;
  startDate: string;
  endDate: string;
  description?: string;
  location?: string;
  dateStr?: string;
  timeStr?: string;
  image_url?: string;
  price?: string;
  instructor?: string;
  registration?: string;
}

interface EventEditorProps {
  isOpen: boolean;
  onClose: () => void;
}

const EventEditor: React.FC<EventEditorProps> = ({ isOpen, onClose }) => {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error' | ''>('');
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [newEvent, setNewEvent] = useState<Event>({
    title: '',
    startDate: '',
    endDate: '',
    description: '',
    location: '',
    dateStr: '',
    timeStr: '',
    image_url: "/logo192.png",
    price: '',
    instructor: '',
    registration: ''
  });

  // Auto-load events when editor opens and user is authenticated
  useEffect(() => {
    if (isOpen && isAuthenticated) {
      loadScrapedEvents();
    }
  }, [isOpen, isAuthenticated]);

  // Check if user is authenticated (simple password check)
  const checkAuthentication = () => {
    const correctPassword = 'rebecca2025'; // Change this to your preferred password
    return password === correctPassword;
  };

  const handleLogin = () => {
    if (checkAuthentication()) {
      setIsAuthenticated(true);
      setMessage('Access granted! You can now edit events.');
      setMessageType('success');
    } else {
      setMessage('Incorrect password. Only authorized users can edit events.');
      setMessageType('error');
    }
  };

  // Load events from backend
  const loadEvents = async () => {
    setLoading(true);
    try {
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events');
              if (response.ok) {
                const data = await response.json();
                const events = data.events || [];
                // Ensure all events have image URLs
                const eventsWithImages = events.map((event: any) => ({
                  ...event,
                  image_url: event.image_url || '/event-schedule-banner.png'
                }));
                setEvents(eventsWithImages);
                setMessage(`Loaded ${events.length} events from backend`);
                setMessageType('success');
              } else {
                throw new Error('Failed to load events');
              }
    } catch (error) {
      console.error('Error loading events:', error);
      setMessage('Failed to load events');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  // Load scraped events from backend API
  const loadScrapedEvents = async () => {
    setLoading(true);
    try {
      // Load events from the backend API (which includes all current events)
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events');
      if (response.ok) {
        const data = await response.json();
        const backendEvents = data.events || [];
        if (backendEvents.length > 0) {
          // Convert backend events to frontend format
          const convertedEvents = backendEvents.map((event: any) => ({
            id: event.id,
            title: event.title,
            startDate: event.startDate,
            endDate: event.endDate,
            description: event.description || '',
            location: event.location || '',
            dateStr: event.dateStr || '',
            timeStr: event.timeStr || '',
            image_url: event.image_url || '/logo192.png',
            price: event.price || '',
            instructor: event.instructor || '',
            registration: event.registration || ''
          }));
          
          setEvents(convertedEvents);
          setMessage(`✅ Loaded ${convertedEvents.length} events from backend!`);
          setMessageType('success');
          return;
        } else {
          setMessage('❌ No events found in backend');
          setMessageType('error');
          return;
        }
      } else {
        setMessage(`❌ Failed to load events: ${response.statusText}`);
        setMessageType('error');
        return;
      }
      
      // Fallback: Try to load from the actual scraped file
      try {
        const response = await fetch('/editable_events.json');
        if (response.ok) {
          const data = await response.json();
          const scrapedEvents = data.events || [];
          if (scrapedEvents.length > 0) {
            // Check if the scraped events have proper details (not just TBA)
            const hasProperDetails = scrapedEvents.some((event: any) => 
              event.timeStr && event.timeStr !== 'TBA' && 
              event.description && event.description.trim() !== ''
            );
            
            if (hasProperDetails) {
              // Ensure all events have image URLs
              const eventsWithImages = scrapedEvents.map((event: any) => ({
                ...event,
                image_url: event.image_url || '/logo192.png'
              }));
              setEvents(eventsWithImages);
              setMessage(`✅ Loaded ${scrapedEvents.length} scraped events from file!`);
              setMessageType('success');
              return;
            } else {
              console.log('Scraped events have incomplete details, using fallback events');
            }
          }
        }
      } catch (error) {
        console.log('Could not load scraped file, using fallback events');
      }

      // Fallback to comprehensive events with complete details
      const newEvents = [
        {
          title: "Daylight Savings Ends",
          startDate: "2025-11-02T08:00:00Z",
          endDate: "2025-11-02T09:00:00Z",
          description: "Daylight saving time ends. Clocks fall back one hour.",
          location: "Everywhere",
          dateStr: "November 2",
          timeStr: "8:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Online Registration Begins",
          startDate: "2025-11-03T08:00:00Z",
          endDate: "2025-11-03T09:00:00Z",
          description: "Online Program Registration Starts Today",
          location: "Online",
          dateStr: "November 3",
          timeStr: "8:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Assistive Listening Solutions",
          startDate: "2025-11-03T12:00:00Z",
          endDate: "2025-11-03T13:00:00Z",
          description: "Removing communication barriers leads to engagement within the community. Learn about how assistive listening solutions can help hard-of-hearing members remove background noise and hear what they are intended to. This session will provide an overview of the solutions available today and how they can benefit those who struggle to hear in public spaces.",
          location: "Seniors Kingston Centre",
          dateStr: "November 3",
          timeStr: "12:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "In-Person Registration for Session 2 Begins",
          startDate: "2025-11-04T08:30:00Z",
          endDate: "2025-11-04T09:30:00Z",
          description: "In-person and mail registration begins Monday November 3 at 8:30am. Session 2 begins November 27.",
          location: "Seniors Kingston Centre",
          dateStr: "November 4",
          timeStr: "8:30 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Fresh Food Market",
          startDate: "2025-11-04T10:00:00Z",
          endDate: "2025-11-04T11:00:00Z",
          description: "Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
          location: "Seniors Kingston Centre",
          dateStr: "November 4",
          timeStr: "10:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Fraud Awareness",
          startDate: "2025-11-05T13:00:00Z",
          endDate: "2025-11-05T14:00:00Z",
          description: "Protect your money and identity from phone, internet, and in-person fraudsters. Learn how to spot and avoid scams.",
          location: "Seniors Kingston Centre",
          dateStr: "November 5",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Cut. Fold. Glue. Stars.",
          startDate: "2025-11-06T11:30:00Z",
          endDate: "2025-11-06T12:30:00Z",
          description: "Join Carole and learn to make charming loo roll snowflakes to bring whimsy to your winter decor.",
          location: "Seniors Kingston Centre",
          dateStr: "November 6",
          timeStr: "11:30 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Learn about Tarot",
          startDate: "2025-11-06T13:00:00Z",
          endDate: "2025-11-06T14:00:00Z",
          description: "Tarocchini is a card game where trumps take tricks. Created in 1400 in Italy, it has evolved into games like Bridge. Is Tarot a game of fortune telling, tricks, or a psychological study? Come play and decide.",
          location: "Seniors Kingston Centre",
          dateStr: "November 6",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Hearing Clinic",
          startDate: "2025-11-07T09:00:00Z",
          endDate: "2025-11-07T10:00:00Z",
          description: "Holly Brooks, Hearing Instrument Specialist, from Hear Right Canada provides hearing tests and hearing aid cleaning. Batteries also available for a fee. Appointments required.",
          location: "Seniors Kingston Centre",
          dateStr: "November 7",
          timeStr: "9:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Coffee with a Cop",
          startDate: "2025-11-07T10:00:00Z",
          endDate: "2025-11-07T11:00:00Z",
          description: "Join Constable Anthony Colangeli for coffee and conversation. Ask questions and voice concerns. Walk-in. All are welcome.",
          location: "Seniors Kingston Centre",
          dateStr: "November 7",
          timeStr: "10:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Cut. Fold. Glue. Trees",
          startDate: "2025-11-10T10:45:00Z",
          endDate: "2025-11-10T11:45:00Z",
          description: "Join Carole and learn to make fanciful paper trees for your holiday tablescapes.",
          location: "Seniors Kingston Centre",
          dateStr: "November 10",
          timeStr: "10:45 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Shopping & Buying Online",
          startDate: "2025-11-10T12:00:00Z",
          endDate: "2025-11-10T13:00:00Z",
          description: "Dip your toes into online shopping. Learn how to get the most out of online stores, how to comparison shop and making informed purchases and how to choose streaming services for movies and TV programs.",
          location: "Seniors Kingston Centre",
          dateStr: "November 10",
          timeStr: "12:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Legal Advice",
          startDate: "2025-11-10T13:00:00Z",
          endDate: "2025-11-10T14:00:00Z",
          description: "A practicing lawyer provides confidential advice by phone. Appointment required (20 minutes max).",
          location: "Seniors Kingston Centre",
          dateStr: "November 10",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Fresh Food Market",
          startDate: "2025-11-11T10:00:00Z",
          endDate: "2025-11-11T11:00:00Z",
          description: "Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
          location: "Seniors Kingston Centre",
          dateStr: "November 11",
          timeStr: "10:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Service Canada Clinic",
          startDate: "2025-11-12T09:00:00Z",
          endDate: "2025-11-12T10:00:00Z",
          description: "Service Canada representatives come to The Seniors Centre to help you with Canadian Pension Plan (CPP), Old Age Security (OAS), Guaranteed Income Supplement (GIS), Social Insurance Number (SIN), or Canadian Dental Care Plan.",
          location: "Seniors Kingston Centre",
          dateStr: "November 12",
          timeStr: "9:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Coast to Coast: A Canoe Odyssey",
          startDate: "2025-11-13T13:00:00Z",
          endDate: "2025-11-13T14:00:00Z",
          description: "Two paddlers, one canoe, and 8,500 km from Vancouver to Sydney – through cities, towns, and wild terrain. Hear about this epic adventure of resilience, connection, and discovery across Canada's diverse landscapes and waterways.",
          location: "Seniors Kingston Centre",
          dateStr: "November 13",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Birthday Lunch",
          startDate: "2025-11-14T12:00:00Z",
          endDate: "2025-11-14T13:00:00Z",
          description: "Members celebrate their birthday month for free!",
          location: "Seniors Kingston Centre",
          dateStr: "November 14",
          timeStr: "12:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Sound Escapes: Georgette Fry",
          startDate: "2025-11-14T13:30:00Z",
          endDate: "2025-11-14T14:30:00Z",
          description: "Experience the award-winning Georgette Fry's soulful blend of blues, jazz, and pop. Her electrifying style will have you up and dancing all afternoon long!",
          location: "Seniors Kingston Centre",
          dateStr: "November 14",
          timeStr: "1:30 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Program Break Week",
          startDate: "2025-11-17T08:30:00Z",
          endDate: "2025-11-17T09:30:00Z",
          description: "No programs are scheduled at any Seniors Association locations.",
          location: "All Locations",
          dateStr: "November 17",
          timeStr: "8:30 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Speed Friending",
          startDate: "2025-11-17T13:00:00Z",
          endDate: "2025-11-17T14:00:00Z",
          description: "Meet new people quickly in a fun, structured setting with speed friending, a platonic twist on speed dating. Rotate through brief conversations, connect with others, and potentially form lasting friendships in just minutes.",
          location: "Seniors Kingston Centre",
          dateStr: "November 17",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Advanced Care Planning",
          startDate: "2025-11-17T16:30:00Z",
          endDate: "2025-11-17T17:30:00Z",
          description: "The process of thinking about, writing down, and sharing your wishes/instructions with loved ones for future health care treatment if you become incapable of deciding for yourself. Learn, listen, and ask questions to help you improve your plan.",
          location: "Seniors Kingston Centre",
          dateStr: "November 17",
          timeStr: "4:30 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Fresh Food Market",
          startDate: "2025-11-18T10:00:00Z",
          endDate: "2025-11-18T11:00:00Z",
          description: "Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
          location: "Seniors Kingston Centre",
          dateStr: "November 18",
          timeStr: "10:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Expressive Mark Making",
          startDate: "2025-11-18T13:00:00Z",
          endDate: "2025-11-18T14:00:00Z",
          description: "Rekindle your passion for abstract art through expressive mark-making. This liberating workshop uses skill-building exercises and soul-nurturing prompts to unlock your subconscious, inspire creativity, and help you rediscover your unique, lyrical style.",
          location: "Seniors Kingston Centre",
          dateStr: "November 18",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Cafe Franglish",
          startDate: "2025-11-18T14:30:00Z",
          endDate: "2025-11-18T15:30:00Z",
          description: "Join a monthly bilingual meetup where Francophones and Anglophones connect chat, and build confidence in both languages through lively, judgement-free conversations on a variety of engaging topics.",
          location: "Seniors Kingston Centre",
          dateStr: "November 18",
          timeStr: "2:30 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Tuesday at Tom's",
          startDate: "2025-11-18T15:00:00Z",
          endDate: "2025-11-18T16:00:00Z",
          description: "New to town or looking to make new friends? Come and enjoy a relaxing conversation and beverage with other members.",
          location: "Seniors Kingston Centre",
          dateStr: "November 18",
          timeStr: "3:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Learn Resilience",
          startDate: "2025-11-19T09:30:00Z",
          endDate: "2025-11-19T10:30:00Z",
          description: "Experience the award-winning documentary Resilience, then join Teach Resilience trainers from Kingston Community Health Centres for an engaging panel discussion of the film, speaking about trauma and its impact.",
          location: "Seniors Kingston Centre",
          dateStr: "November 19",
          timeStr: "9:30 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Vision Workshop",
          startDate: "2025-11-19T10:30:00Z",
          endDate: "2025-11-19T11:30:00Z",
          description: "Rediscover purpose, passion, and joy in retirement. Learn simple tools to dream again, break free from \"too late\" thinking, and design a vibrant next chapter – filled with meaning, connection, and confidence.",
          location: "Seniors Kingston Centre",
          dateStr: "November 19",
          timeStr: "10:30 AM",
          image_url: "/logo192.png"
        },
        {
          title: "New Member Mixer",
          startDate: "2025-11-19T14:00:00Z",
          endDate: "2025-11-19T15:00:00Z",
          description: "Are you a new member and want to learn more about what we offer? Have a friend you'd like to join? Or do you just want to know more about the Seniors Association? Meet with staff and other members for a brief orientation, introduction to our database, light refreshments, and socializing.",
          location: "Seniors Kingston Centre",
          dateStr: "November 19",
          timeStr: "2:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Time for Tea",
          startDate: "2025-11-20T13:00:00Z",
          endDate: "2025-11-20T14:00:00Z",
          description: "Explore the fine art of tea and food pairing with a certified tea sommelier. Discover how nuanced flavors enhance cuisine through expertly selected teas and culinary harmony over the Holiday season.",
          location: "Seniors Kingston Centre",
          dateStr: "November 20",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Book & Puzzle EXCHANGE",
          startDate: "2025-11-21T10:00:00Z",
          endDate: "2025-11-21T11:00:00Z",
          description: "Bring up to 10 paperback books or puzzles to the Rendezvous Café to exchange for any in our library. Additional books or puzzles can be purchased for $2.",
          location: "Seniors Kingston Centre",
          dateStr: "November 21",
          timeStr: "10:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Annual General Meeting",
          startDate: "2025-11-21T11:00:00Z",
          endDate: "2025-11-21T12:00:00Z",
          description: "The theme for the 49th Annual General Meeting is Strategic Growth for Future Success and will be held at The Seniors Centre.",
          location: "Seniors Kingston Centre",
          dateStr: "November 21",
          timeStr: "11:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "December Vista Available for Pickup",
          startDate: "2025-11-21T12:00:00Z",
          endDate: "2025-11-21T13:00:00Z",
          description: "Volunteer Deliverers pick up their bundles to hand deliver and members can pick up their individual copy.",
          location: "Seniors Kingston Centre",
          dateStr: "November 21",
          timeStr: "12:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Holiday Artisan Fair",
          startDate: "2025-11-22T10:00:00Z",
          endDate: "2025-11-22T11:00:00Z",
          description: "Something for everyone!",
          location: "Seniors Kingston Centre",
          dateStr: "November 22",
          timeStr: "10:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Simplify Your Digital Life",
          startDate: "2025-11-24T12:00:00Z",
          endDate: "2025-11-24T13:00:00Z",
          description: "Feeling overwhelmed by your online accounts, passwords, and subscriptions? This presentation offers practical strategies to simplify your digital life. Learn to organize accounts, manage passwords, use cloud storage effectively, and understand your subscriptions. We'll also explore options for closing services you no longer need – empowering you to take control of your digital world.",
          location: "Seniors Kingston Centre",
          dateStr: "November 24",
          timeStr: "12:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Legal Advice",
          startDate: "2025-11-24T13:00:00Z",
          endDate: "2025-11-24T14:00:00Z",
          description: "A practicing lawyer provides confidential advice by phone. Appointment required (20 minutes max).",
          location: "Seniors Kingston Centre",
          dateStr: "November 24",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Fresh Food Market",
          startDate: "2025-11-25T10:00:00Z",
          endDate: "2025-11-25T11:00:00Z",
          description: "Lionhearts brings fresh, affordable produce and chef-created gourmet healthy options to The Seniors Centre to help you keep your belly full without emptying your wallet.",
          location: "Seniors Kingston Centre",
          dateStr: "November 25",
          timeStr: "10:00 AM",
          image_url: "/logo192.png"
        },
        {
          title: "Holiday Lunch",
          startDate: "2025-11-25T12:00:00Z",
          endDate: "2025-11-25T13:00:00Z",
          description: "Tomato Basil Soup, Roast Turkey, dressing, mashed potatoes, vegetables, cranberry sauce, and dessert!",
          location: "Seniors Kingston Centre",
          dateStr: "November 25",
          timeStr: "12:00 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Domino Theatre Dress Rehearsal: Miss Bennet: Christmas at Pemberley",
          startDate: "2025-11-26T19:30:00Z",
          endDate: "2025-11-26T20:30:00Z",
          description: "Celebrate the holidays with a witty sequel to Pride and Prejudice, where overlooked Mary Bennet discovers romance at Pemberley. Full of heart, humour, and Regency charm, this play delights.",
          location: "Domino Theatre",
          dateStr: "November 26",
          timeStr: "7:30 PM",
          image_url: "/logo192.png"
        },
        {
          title: "Anxiety Unlocked",
          startDate: "2025-11-27T13:00:00Z",
          endDate: "2025-11-27T14:00:00Z",
          description: "Discover fun, easy-to-use tools that bring quick relief from anxiety. Learn simple, effective techniques you may not know, designed to calm your mind, ease stress, and restore balance anytime, anywhere.",
          location: "Seniors Kingston Centre",
          dateStr: "November 27",
          timeStr: "1:00 PM",
          image_url: "/logo192.png"
        }
      ];
      
      setEvents(newEvents);
      setMessage(`Loaded ${newEvents.length} new events with complete details and descriptions!`);
      setMessageType('success');
    } catch (error) {
      console.error('Error loading scraped events:', error);
      setMessage('Failed to load scraped events');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  // Save events to backend
  const saveEvents = async () => {
    setSaving(true);
    try {
      const response = await fetch('https://class-cancellation-backend.onrender.com/api/events/bulk-update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ events }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setMessage(`✅ Successfully saved ${events.length} events to backend! November events are now available in the calendar.`);
          setMessageType('success');
        } else {
          throw new Error(result.error || 'Save failed');
        }
      } else {
        const errorText = await response.text();
        throw new Error(`Save failed: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error saving events:', error);
      setMessage(`❌ Failed to save events: ${error}`);
      setMessageType('error');
    } finally {
      setSaving(false);
    }
  };

  // Add new event
  const addEvent = () => {
    if (!newEvent.title || !newEvent.startDate || !newEvent.endDate) {
      setMessage('Please fill in required fields (title, start date, end date)');
      setMessageType('error');
      return;
    }

    const event: Event = {
      ...newEvent,
      id: `event_${Date.now()}`,
    };

    setEvents([...events, event]);
    setNewEvent({
      title: '',
      startDate: '',
      endDate: '',
      description: '',
      location: '',
      dateStr: '',
      timeStr: '',
      image_url: "/logo192.png",
      price: '',
      instructor: '',
      registration: ''
    });
    setMessage('Event added successfully');
    setMessageType('success');
  };

  // Edit event
  const editEvent = (index: number) => {
    setEditingIndex(index);
    setNewEvent(events[index]);
  };

  // Update event
  const updateEvent = () => {
    if (editingIndex === null || !newEvent.title || !newEvent.startDate || !newEvent.endDate) {
      setMessage('Please fill in required fields');
      setMessageType('error');
      return;
    }

    const updatedEvents = [...events];
    updatedEvents[editingIndex] = { ...newEvent };
    setEvents(updatedEvents);
    setEditingIndex(null);
    setNewEvent({
      title: '',
      startDate: '',
      endDate: '',
      description: '',
      location: '',
      dateStr: '',
      timeStr: '',
      image_url: "/logo192.png",
      price: '',
      instructor: '',
      registration: ''
    });
    setMessage('Event updated successfully');
    setMessageType('success');
  };

  // Delete event
  const deleteEvent = (index: number) => {
    if (window.confirm('Are you sure you want to delete this event?')) {
      const updatedEvents = events.filter((_, i) => i !== index);
      setEvents(updatedEvents);
      setMessage('Event deleted successfully');
      setMessageType('success');
    }
  };

  // Cancel edit
  const cancelEdit = () => {
    setEditingIndex(null);
    setNewEvent({
      title: '',
      startDate: '',
      endDate: '',
      description: '',
      location: '',
      dateStr: '',
      timeStr: '',
      image_url: "/logo192.png",
      price: '',
      instructor: '',
      registration: ''
    });
  };

  // Load events when modal opens
  useEffect(() => {
    if (isOpen) {
      loadEvents();
    }
  }, [isOpen]);

  // Clear message after 3 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage('');
        setMessageType('');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  if (!isOpen) return null;

  return (
    <div className="event-editor-overlay" onClick={onClose}>
      <div className="event-editor-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="event-editor-header">
          <h2>Event Editor</h2>
          <button className="event-editor-close" onClick={onClose}>×</button>
        </div>

        {/* Authentication */}
        {!isAuthenticated ? (
          <div className="event-editor-auth">
            <h3>🔒 Admin Access Required</h3>
            <p>Enter password to edit events:</p>
            <div className="auth-form">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
              />
              <button onClick={handleLogin}>Login</button>
            </div>
            <p className="auth-note">Only authorized users can edit events</p>
          </div>
        ) : (
          <>
            {/* Message */}
            {message && (
              <div className={`event-editor-message ${messageType}`}>
                {message}
              </div>
            )}

        {/* Controls */}
        <div className="event-editor-controls">
          <button 
            onClick={loadEvents} 
            disabled={loading}
            className="event-editor-button event-editor-button-secondary"
          >
            {loading ? 'Loading...' : '🔄 Load Backend Events'}
          </button>
          <button 
            onClick={loadScrapedEvents} 
            disabled={loading}
            className="event-editor-button event-editor-button-success"
          >
            {loading ? 'Loading...' : '📥 Load New Events'}
          </button>
          <button 
            onClick={saveEvents} 
            disabled={saving || events.length === 0}
            className="event-editor-button event-editor-button-primary"
          >
            {saving ? 'Saving...' : `💾 Save ${events.length} Events`}
          </button>
        </div>

        {/* Add/Edit Event Form */}
        <div className="event-editor-form">
          <h3>{editingIndex !== null ? 'Edit Event' : 'Add New Event'}</h3>
          
          <div className="event-editor-form-row">
            <div className="event-editor-form-group">
              <label>Event ID</label>
              <input
                type="text"
                value={newEvent.id || ''}
                onChange={(e) => setNewEvent({ ...newEvent, id: e.target.value })}
                placeholder="Event ID (optional)"
              />
            </div>
            <div className="event-editor-form-group">
              <label>Title *</label>
              <input
                type="text"
                value={newEvent.title}
                onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                placeholder="Event title"
              />
            </div>
          </div>

          <div className="event-editor-form-row">
            <div className="event-editor-form-group">
              <label>Location</label>
              <input
                type="text"
                value={newEvent.location || ''}
                onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                placeholder="Event location"
              />
            </div>
            <div className="event-editor-form-group">
              <label>Image URL</label>
              <input
                type="text"
                value={newEvent.image_url || ''}
                onChange={(e) => setNewEvent({ ...newEvent, image_url: e.target.value })}
                placeholder="Image URL or path"
              />
            </div>
          </div>

          <div className="event-editor-form-row">
            <div className="event-editor-form-group">
              <label>Start Date *</label>
              <input
                type="datetime-local"
                value={newEvent.startDate}
                onChange={(e) => setNewEvent({ ...newEvent, startDate: e.target.value })}
              />
            </div>
            <div className="event-editor-form-group">
              <label>End Date *</label>
              <input
                type="datetime-local"
                value={newEvent.endDate}
                onChange={(e) => setNewEvent({ ...newEvent, endDate: e.target.value })}
              />
            </div>
          </div>

          <div className="event-editor-form-group">
            <label>Description</label>
            <textarea
              value={newEvent.description || ''}
              onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
              placeholder="Event description"
              rows={3}
            />
          </div>

          <div className="event-editor-form-row">
            <div className="event-editor-form-group">
              <label>Date String</label>
              <input
                type="text"
                value={newEvent.dateStr || ''}
                onChange={(e) => setNewEvent({ ...newEvent, dateStr: e.target.value })}
                placeholder="e.g., November 15"
              />
            </div>
            <div className="event-editor-form-group">
              <label>Time String</label>
              <input
                type="text"
                value={newEvent.timeStr || ''}
                onChange={(e) => setNewEvent({ ...newEvent, timeStr: e.target.value })}
                placeholder="e.g., 2:00 PM"
              />
            </div>
          </div>

          <div className="event-editor-form-row">
            <div className="event-editor-form-group">
              <label>Price</label>
              <input
                type="text"
                value={newEvent.price || ''}
                onChange={(e) => setNewEvent({ ...newEvent, price: e.target.value })}
                placeholder="e.g., $15, Free, $25"
              />
            </div>
            <div className="event-editor-form-group">
              <label>Instructor</label>
              <input
                type="text"
                value={newEvent.instructor || ''}
                onChange={(e) => setNewEvent({ ...newEvent, instructor: e.target.value })}
                placeholder="Instructor name"
              />
            </div>
          </div>

          <div className="event-editor-form-group">
            <label>Registration Info</label>
            <input
              type="text"
              value={newEvent.registration || ''}
              onChange={(e) => setNewEvent({ ...newEvent, registration: e.target.value })}
              placeholder="e.g., Call 613-548-7810, Online registration required"
            />
          </div>

          <div className="event-editor-form-actions">
            {editingIndex !== null ? (
              <>
                <button onClick={updateEvent} className="event-editor-button event-editor-button-primary">
                  Update Event
                </button>
                <button onClick={cancelEdit} className="event-editor-button event-editor-button-secondary">
                  Cancel
                </button>
              </>
            ) : (
              <button onClick={addEvent} className="event-editor-button event-editor-button-primary">
                Add Event
              </button>
            )}
          </div>
        </div>

        {/* Events List */}
        <div className="event-editor-list">
          <h3>Current Events ({events.length})</h3>
          {events.length === 0 ? (
            <div className="event-editor-empty">
              <p>No events found. Click "Load Backend Events" or "Load New Events" to load events.</p>
              <p>Or add new events using the form above.</p>
            </div>
          ) : (
            <div className="event-editor-events">
              {events.map((event, index) => (
                <div key={event.id || index} className="event-editor-event">
                  <div className="event-editor-event-info">
                    <h4>{event.title}</h4>
                    <p><strong>Date:</strong> {event.dateStr || new Date(event.startDate).toLocaleDateString()}</p>
                    <p><strong>Time:</strong> {event.timeStr || new Date(event.startDate).toLocaleTimeString()}</p>
                    {event.location && <p><strong>Location:</strong> {event.location}</p>}
                    {event.price && <p><strong>Price:</strong> {event.price}</p>}
                    {event.instructor && <p><strong>Instructor:</strong> {event.instructor}</p>}
                    {event.registration && <p><strong>Registration:</strong> {event.registration}</p>}
                    {event.description && <p><strong>Description:</strong> {event.description.substring(0, 100)}...</p>}
                  </div>
                  <div className="event-editor-event-actions">
                    <button 
                      onClick={() => editEvent(index)}
                      className="event-editor-button event-editor-button-small event-editor-button-secondary"
                    >
                      Edit
                    </button>
                    <button 
                      onClick={() => deleteEvent(index)}
                      className="event-editor-button event-editor-button-small event-editor-button-danger"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
          </>
        )}
      </div>
    </div>
  );
};

export default EventEditor;
