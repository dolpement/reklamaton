import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './App.css';

const App = () => {
  // Состояние аутентификации
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authMode, setAuthMode] = useState('login'); // 'login' или 'register'
  const [authForm, setAuthForm] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Состояние приложения (из старого интерфейса)
  const [currentView, setCurrentView] = useState('chats');
  const [selectedChat, setSelectedChat] = useState(null);
  const [isInCall, setIsInCall] = useState(false);
  const [callType, setCallType] = useState(null);
  const [showCreateAgent, setShowCreateAgent] = useState(false);
  const [newAgentData, setNewAgentData] = useState({
    name: "",
    description: "",
    character: "",
    emoji: ""
  });
  
  // Состояние дрона
  const [droneStatus, setDroneStatus] = useState('disconnected');
  const [isMuted, setIsMuted] = useState(false);
  // Состояние чата с AI агентами
  const [chatMessages, setChatMessages] = useState({});
  const [currentMessage, setCurrentMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Состояние поиска
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  // Socket.IO и WebRTC
  const [socket, setSocket] = useState(null);
  const [connectedUsers, setConnectedUsers] = useState([]);
  const [incomingCall, setIncomingCall] = useState(null);
  const [currentCall, setCurrentCall] = useState(null);
  const currentCallRef = useRef(currentCall); // Добавляем ref для currentCall
  useEffect(() => {
    currentCallRef.current = currentCall;
  }, [currentCall]);
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const localStreamRef = useRef(null);

  // Данные AI агентов
  const [aiAgents, setAiAgents] = useState([
    { id: 'founder', name: 'Founder', description: 'Опытный предприниматель', emoji: '👨‍💼', character: 'business' },
    { id: 'foundersha', name: 'Foundersha', description: 'Женщина-предприниматель', emoji: '👩‍💼', character: 'creative' },
    { id: 'creeper', name: 'Крипер', description: 'Загадочный персонаж', emoji: '👾', character: 'mystery' },
    { id: 'twinby', name: 'Twinby', description: 'Двойник с идеями', emoji: '👥', character: 'innovation' },
    { id: 'wise_advisor', name: 'Мудрый Советник', description: 'Опытный наставник и мудрый советник', emoji: '🧙‍♂️', character: 'Ты мудрый и опытный наставник с глубокими знаниями в различных областях жизни. Ты говоришь спокойно и размеренно, даешь продуманные советы и всегда готов выслушать. Твоя речь полна мудрости и жизненного опыта. Ты терпелив, добр и понимающий. Любишь использовать притчи и метафоры для объяснения сложных вещей.' },
  ]);

  // Тестовые пользователи для демонстрации
  const [testUsers] = useState([
    { 
      id: 'user1', 
      username: 'Анна Петрова', 
      is_online: true, 
      last_seen: new Date().toISOString(),
      avatar: '👩‍💻'
    },
    { 
      id: 'user2', 
      username: 'Михаил Иванов', 
      is_online: true, 
      last_seen: new Date(Date.now() - 300000).toISOString(),
      avatar: '👨‍🎨'
    },
    { 
      id: 'user3', 
      username: 'Елена Сидорова', 
      is_online: false, 
      last_seen: new Date(Date.now() - 3600000).toISOString(),
      avatar: '👩‍🔬'
    },
    { 
      id: 'user4', 
      username: 'Дмитрий Козлов', 
      is_online: true, 
      last_seen: new Date(Date.now() - 120000).toISOString(),
      avatar: '👨‍💼'
    },
    { 
      id: 'user5', 
      username: 'Ольга Морозова', 
      is_online: false, 
      last_seen: new Date(Date.now() - 7200000).toISOString(),
      avatar: '👩‍🎓'
    }
  ]);

  // Тестовые сообщения для демонстрации
  const [testMessages] = useState({
    'user1': [
      {
        id: 1,
        text: 'Привет! Как дела?',
        role: 'user',
        timestamp: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 2,
        text: 'Привет! Все отлично, работаю над новым проектом. А у тебя как?',
        role: 'assistant',
        timestamp: new Date(Date.now() - 3500000).toISOString()
      },
      {
        id: 3,
        text: 'Тоже хорошо! Расскажи про проект',
        role: 'user',
        timestamp: new Date(Date.now() - 3400000).toISOString()
      }
    ],
    'user2': [
      {
        id: 1,
        text: 'Добрый день! Не могли бы вы помочь с одним вопросом?',
        role: 'user',
        timestamp: new Date(Date.now() - 1800000).toISOString()
      },
      {
        id: 2,
        text: 'Конечно! Слушаю вас',
        role: 'assistant',
        timestamp: new Date(Date.now() - 1700000).toISOString()
      }
    ],
    'user4': [
      {
        id: 1,
        text: 'Отличная встреча сегодня была!',
        role: 'user',
        timestamp: new Date(Date.now() - 600000).toISOString()
      },
      {
        id: 2,
        text: 'Да, согласен! Много интересных идей обсудили',
        role: 'assistant',
        timestamp: new Date(Date.now() - 500000).toISOString()
      },
      {
        id: 3,
        text: 'Когда планируем следующую?',
        role: 'user',
        timestamp: new Date(Date.now() - 400000).toISOString()
      }
    ]
  });


  // Проверка аутентификации при загрузке
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Инициализация Socket.IO после аутентификации
  useEffect(() => {
    if (isAuthenticated && !socket) {
      const newSocket = io('http://localhost:3001', {
        withCredentials: true
      });
      setSocket(newSocket);

      newSocket.on('connect', () => {
        console.log('Socket connected:', newSocket.id);
        newSocket.emit('authenticate'); // Отправляем событие аутентификации
      });

      newSocket.on('authenticated', (data) => {
        console.log('Socket authenticated:', data);
        // Обновляем список пользователей после успешной аутентификации
        newSocket.emit('get_online_users');
      });

      newSocket.on('online_users', (users) => {
        // Фильтруем текущего пользователя из списка
        setConnectedUsers(users.filter(user => user.id !== currentUser?.id));
      });

      newSocket.on('user_connected', (user) => {
        if (user.id !== currentUser?.id) {
          setConnectedUsers(prev => [...prev, user]);
        }
      });

      newSocket.on('user_disconnected', (data) => {
        setConnectedUsers(prev => prev.filter(user => user.id !== data.user_id));
      });

      newSocket.on('incoming_call', (data) => {
        setIncomingCall(data);
      });

      newSocket.on('call_accepted', (data) => {
        setCurrentCall(data);
        setIncomingCall(null);
        if (data.call_id) {
          initializeWebRTC(data.call_id, false, data.type); // Передаем тип звонка
        }
      });

      newSocket.on('call_declined', () => {
        setCurrentCall(null);
        setIncomingCall(null);
        alert('Звонок отклонен');
      });

      newSocket.on('call_ended', () => {
        endCall();
      });

      newSocket.on('drone_status_update', (data) => {
        setDroneStatus(data.status);
      });

      // WebRTC события
      newSocket.on("webrtc_offer", async ({ call_id, offer, from: senderSocketId }) => {
        const currentCallData = currentCallRef.current; // Используем ref для актуального состояния
        if (currentCallData && currentCallData.call_id === call_id) {
          try {
            await peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription(offer));
            const answer = await peerConnectionRef.current.createAnswer();
            await peerConnectionRef.current.setLocalDescription(answer);
            newSocket.emit("webrtc_answer", { call_id, answer });
          } catch (error) {
            console.error("Error setting remote offer or creating answer:", error);
          }
        }
      });

      newSocket.on("webrtc_answer", async ({ call_id, answer }) => {
        const currentCallData = currentCallRef.current; // Используем ref для актуального состояния
        if (currentCallData && currentCallData.call_id === call_id) {
          try {
            await peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription(answer));
          } catch (error) {
            console.error("Error setting remote answer:", error);
          }
        }
      });

      newSocket.on("webrtc_ice_candidate", async ({ call_id, candidate }) => {
        const currentCallData = currentCallRef.current; // Используем ref для актуального состояния
        if (currentCallData && currentCallData.call_id === call_id) {
          try {
            await peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(candidate));
          } catch (error) {
            console.error("Error adding received ICE candidate:", error);
          }
        }
      });

      return () => {
        newSocket.disconnect();
      };
    }
  }, [isAuthenticated, currentUser, socket, currentCall]); // Добавил socket и currentCall в зависимости

  // Проверка статуса аутентификации
  const checkAuthStatus = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/profile', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentUser(data.user);
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
        setCurrentUser(null);
      }
    } catch (error) {
      console.error('Ошибка проверки аутентификации:', error);
      setIsAuthenticated(false);
      setCurrentUser(null);
    }
  };

  // Обработка формы аутентификации
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);

    const endpoint = authMode === 'login' ? '/api/login' : '/api/register';
    const payload = authMode === 'login' 
      ? { username: authForm.username, password: authForm.password }
      : authForm;

    try {
      const response = await fetch(`http://localhost:3001${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        setCurrentUser(data.user);
        setIsAuthenticated(true);
        setAuthForm({ username: '', email: '', password: '' });
        // После успешной аутентификации, запросить список онлайн пользователей
        if (socket) {
          socket.emit('get_online_users');
        }
      } else {
        setAuthError(data.error || 'Ошибка аутентификации');
      }
    } catch (error) {
      setAuthError('Ошибка соединения с сервером');
    } finally {
      setAuthLoading(false);
    }
  };

  // Выход
  const handleLogout = async () => {
    try {
      await fetch('http://localhost:3001/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
      
      if (socket) {
        socket.disconnect();
        setSocket(null);
      }
      
      setIsAuthenticated(false);
      setCurrentUser(null);
      setConnectedUsers([]);
      setCurrentCall(null);
      setIncomingCall(null);
      setSelectedChat(null);
      setIsInCall(false);
      setDroneStatus('disconnected');
      setSearchQuery('');
      setSearchResults([]);
      setShowSearch(false);
    } catch (error) {
      console.error('Ошибка выхода:', error);
    }
  };

  // Поиск пользователей
  const searchUsers = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(`http://localhost:3001/api/search?q=${encodeURIComponent(query)}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.users);
      } else {
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Ошибка поиска:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Обработка изменения поискового запроса
  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Дебаунс для поиска
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      searchUsers(query);
    }, 300);
  };

  // Toggle mute
  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach(track => {
        track.enabled = !track.enabled;
      });
    }
  };

  // Функция для API запросов к дрону с поддержкой потоковой передачи звука
  const droneAPI = async (endpoint, character = null, streamUrl = null) => {
    try {
      setDroneStatus('connecting');
      let url = `http://localhost:3001/api/drone/${endpoint}`;
      
      const params = new URLSearchParams();
      if (character) {
        params.append('character', character);
      }
      if (streamUrl) {
        params.append('streamUrl', streamUrl);
      }
      
      if (params.toString()) {
        url += '?' + params.toString();
      }
      
      const response = await fetch(url);
      if (response.ok) {
        setDroneStatus('connected');
        console.log(`Drone ${endpoint} successful${streamUrl ? ' with stream: ' + streamUrl : ''}`);
        return true;
      } else {
        setDroneStatus('disconnected');
        console.log(`Drone ${endpoint} failed`);
        return false;
      }
    } catch (error) {
      setDroneStatus('disconnected');
      console.log(`Drone ${endpoint} error:`, error);
      return false;
    }
  };

  // Начало звонка с AI агентом
  const startAICall = async (type, agent) => {
    if (!currentUser) return;

    setCurrentCall({
      type: type,
      status: 'connecting',
      participant: agent,
      isAI: true
    });

    setIsInCall(true);

    // Если видеозвонок с AI агентом, подключаемся к дрону
    if (type === 'video') {
      try {
        setDroneStatus('connecting');
        
        // Подключение к дрону через эндпоинт
        const droneResponse = await fetch('http://localhost:3001/api/drone/connect', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            agent_id: agent.id,
            agent_character: agent.character,
            call_type: type
          })
        });

        if (droneResponse.ok) {
          setDroneStatus('connected');
          
          // Инициализируем WebRTC для получения видео с дрона
          await initializeAIWebRTC(agent.id, type);
        } else {
          setDroneStatus('disconnected');
          console.error('Ошибка подключения к дрону');
        }
      } catch (error) {
        setDroneStatus('disconnected');
        console.error('Ошибка подключения к дрону:', error);
      }
    } else {
      // Для аудиозвонка просто устанавливаем соединение
      await initializeAIWebRTC(agent.id, type);
    }

    setCurrentCall(prev => ({
      ...prev,
      status: 'active'
    }));
  };

  // Инициализация WebRTC для AI звонков
  const initializeAIWebRTC = async (agentId, type) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: type === 'video',
        audio: true
      });

      localStreamRef.current = stream;
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Для AI звонков мы можем симулировать удаленный поток
      // или получать его от дрона/сервера
      if (type === 'video' && remoteVideoRef.current) {
        // Здесь можно подключить поток с дрона
        // Пока что создаем пустой поток для демонстрации
        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;
        const ctx = canvas.getContext('2d');
        
        // Рисуем простой фон для демонстрации
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#ffffff';
        ctx.font = '24px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Видео с дрона', canvas.width / 2, canvas.height / 2);
        
        const droneStream = canvas.captureStream(30);
        remoteVideoRef.current.srcObject = droneStream;
      }

    } catch (error) {
      console.error('Ошибка инициализации WebRTC для AI:', error);
      alert('Не удалось получить доступ к камере/микрофону. Проверьте разрешения.');
      endCall();
    }
  };

  // Начало звонка
  const startCall = async (type, contact) => {
    if (!socket || !currentUser) return;

    // Для найденных пользователей через поиск используем их ID
    const calleeId = contact.id || contact.name;

    socket.emit('initiate_call', {
      callee_id: calleeId,
      call_type: type
    });

    setCurrentCall({
      type: type,
      status: 'calling',
      participant: contact
    });

    // Если видеозвонок, активируем дрон
    if (type === 'video') {
      await droneAPI('takeoff');
      const streamUrl = `http://localhost:3001/stream/audio/${calleeId}/${Date.now()}`;
      await droneAPI('audio', 'default', streamUrl);
      await droneAPI('turn', 'default');
    }
  };

  // Принятие звонка
  const acceptCall = async () => {
    if (!socket || !incomingCall) return;

    socket.emit('accept_call', {
      call_id: incomingCall.call_id
    });

    setCurrentCall({
      call_id: incomingCall.call_id,
      type: incomingCall.type,
      status: 'active',
      participant: incomingCall.caller
    });

    setIncomingCall(null);
    await initializeWebRTC(incomingCall.call_id, true, incomingCall.type);

    // Если видеозвонок, активируем дрон
    if (incomingCall.type === 'video') {
      await droneAPI('takeoff');
      const streamUrl = `http://localhost:3001/stream/audio/${incomingCall.caller.id}/${Date.now()}`;
      await droneAPI('audio', 'default', streamUrl);
      await droneAPI('turn', 'default');
    }
  };

  // Отклонение звонка
  const declineCall = () => {
    if (!socket || !incomingCall) return;

    socket.emit('decline_call', {
      call_id: incomingCall.call_id
    });

    setIncomingCall(null);
  };

  // Завершение звонка
  const endCall = () => {
    if (socket && currentCall?.call_id) {
      socket.emit('end_call', {
        call_id: currentCall.call_id
      });
    }

    // Очистка WebRTC
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }

    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
      localStreamRef.current = null;
    }

    setIsInCall(false);
    setCallType(null);
    setCurrentCall(null);
    setDroneStatus('disconnected');
    setSelectedChat(null); // Возвращаемся к списку чатов
  };

  // Инициализация WebRTC
  const initializeWebRTC = async (callId, isInitiator, type) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: type === 'video',
        audio: true
      });

      localStreamRef.current = stream;
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      const peerConnection = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });

      peerConnection.ontrack = (event) => {
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = event.streams[0];
        }
      };

      peerConnection.onicecandidate = (event) => {
        if (event.candidate && socket) {
          socket.emit('webrtc_ice_candidate', {
            call_id: callId,
            candidate: event.candidate
          });
        }
      };

      peerConnectionRef.current = peerConnection;

      stream.getTracks().forEach(track => {
        peerConnection.addTrack(track, stream);
      });

      if (isInitiator) {
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        
        socket.emit('webrtc_offer', {
          call_id: callId,
          offer: offer
        });
      }

    } catch (error) {
      console.error('Ошибка инициализации WebRTC:', error);
      alert('Не удалось получить доступ к камере/микрофону. Проверьте разрешения.');
      endCall(); // Завершаем звонок при ошибке WebRTC
    }
  };



  // Отправка сообщения AI агенту
  const sendMessageToAI = async (message, agentId) => {
    if (!message.trim() || !selectedChat) return;

    const chatId = agentId || selectedChat.id;
    const timestamp = new Date().toISOString();

    // Добавляем сообщение пользователя в чат
    const userMessage = {
      id: Date.now(),
      text: message,
      role: 'user',
      timestamp: timestamp
    };

    setChatMessages(prev => ({
      ...prev,
      [chatId]: [...(prev[chatId] || []), userMessage]
    }));

    setCurrentMessage("");
    setIsTyping(true);

    // Симуляция ответа от AI агента
    setTimeout(() => {
      const aiResponses = [
        "Привет! Я AI агент. Чем могу помочь?",
        "Рад пообщаться! Задавайте свои вопросы.",
        "Я здесь, чтобы помочь вам. Что вас интересует?",
        "Отличный вопрос! Позвольте мне подумать...",
        "Я обрабатываю ваш запрос. Ожидайте ответа."
      ];
      const randomAIResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];

      const aiMessage = {
        id: Date.now() + 1,
        text: randomAIResponse,
        role: "assistant",
        timestamp: new Date().toISOString()
      };

      setChatMessages(prev => ({
        ...prev,
        [chatId]: [...(prev[chatId] || []), userMessage, aiMessage]
      }));
      setIsTyping(false);
    }, 1000 + Math.random() * 2000); // Случайная задержка от 1 до 3 секунд
  };

  // Обработка отправки сообщения
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (currentMessage.trim() && selectedChat) {
      if (selectedChat.character) {
        // Отправка сообщения AI агенту
        sendMessageToAI(currentMessage, selectedChat.id);
      } else {
        // Отправка сообщения обычному пользователю
        sendMessageToUser(currentMessage, selectedChat.id);
      }
    }
  };

  // Отправка сообщения обычному пользователю (симуляция для тестовых пользователей)
  const sendMessageToUser = async (message, userId) => {
    if (!message.trim() || !selectedChat) return;

    const timestamp = new Date().toISOString();

    // Добавляем сообщение пользователя в чат
    const userMessage = {
      id: Date.now(),
      text: message,
      role: 'user',
      timestamp: timestamp
    };

    setChatMessages(prev => ({
      ...prev,
      [userId]: [...(prev[userId] || []), userMessage]
    }));

    setCurrentMessage('');

    // Симуляция ответа для тестовых пользователей
    if (testUsers.find(user => user.id === userId)) {
      setIsTyping(true);
      
      setTimeout(() => {
        const responses = [
          'Спасибо за сообщение! Как дела?',
          'Интересно! Расскажи подробнее',
          'Согласен с тобой',
          'Хорошая идея! Давай обсудим это',
          'Понятно, спасибо за информацию',
          'Да, я тоже так думаю',
          'Отличное предложение!',
          'Нужно подумать над этим'
        ];
        
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        
        const aiMessage = {
          id: Date.now() + 1,
          text: randomResponse,
          role: 'assistant',
          timestamp: new Date().toISOString()
        };

        setChatMessages(prev => ({
          ...prev,
          [userId]: [...(prev[userId] || []), aiMessage]
        }));
        
        setIsTyping(false);
      }, 1000 + Math.random() * 2000); // Случайная задержка от 1 до 3 секунд
    }
  };

  // Создание нового AI агента
  const createNewAgent = () => {
    if (!newAgentData.name || !newAgentData.description || !newAgentData.character) {
      alert('Пожалуйста, заполните все обязательные поля');
      return;
    }

    const newAgent = {
      id: Date.now().toString(),
      name: newAgentData.name,
      description: newAgentData.description,
      character: newAgentData.character,
      emoji: newAgentData.emoji || '🤖'
    };

    setAiAgents(prev => [...prev, newAgent]);
    setNewAgentData({ name: "", description: "", character: "", emoji: "" });
    setShowCreateAgent(false);
  };

  // Рендер формы создания AI агента
  const renderCreateAgentForm = () => (
    <div className="create-agent-overlay">
      <div className="create-agent-form">
        <h2>Создать AI агента</h2>
        
        <div className="form-group">
          <label>Имя агента *</label>
          <input
            type="text"
            placeholder="Введите имя агента"
            value={newAgentData.name}
            onChange={(e) => setNewAgentData({...newAgentData, name: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label>Описание *</label>
          <input
            type="text"
            placeholder="Краткое описание агента"
            value={newAgentData.description}
            onChange={(e) => setNewAgentData({...newAgentData, description: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label>Эмодзи</label>
          <input
            type="text"
            placeholder="🤖"
            value={newAgentData.emoji}
            onChange={(e) => setNewAgentData({...newAgentData, emoji: e.target.value})}
            maxLength="2"
          />
        </div>

        <div className="form-group">
          <label>Характер и личность *</label>
          <textarea
            placeholder="Опишите характер, манеру общения и особенности личности агента..."
            value={newAgentData.character}
            onChange={(e) => setNewAgentData({...newAgentData, character: e.target.value})}
            rows="4"
          />
        </div>

        <div className="form-actions">
          <button 
            className="cancel-btn" 
            onClick={() => setShowCreateAgent(false)}
          >
            Отмена
          </button>
          <button 
            className="create-btn" 
            onClick={createNewAgent}
          >
            Создать агента
          </button>
        </div>
      </div>
    </div>
  );

  // Рендер интерфейса звонка
  const renderCallInterface = () => (
    <div className="call-interface">
      <div className="call-avatar">
        {currentCall.participant.emoji || currentCall.participant.avatar || currentCall.participant.username[0].toUpperCase()}
      </div>
      <h2>{currentCall.participant.username || currentCall.participant.name}</h2>
      <p>{currentCall.type === 'video' ? 'Видеозвонок' : 'Голосовой звонок'}</p>
      
      {currentCall.type === 'video' && (
        <div className={`drone-status ${droneStatus}`}>
          {droneStatus === 'connecting' && '🚁 Подключение дрона...'}
          {droneStatus === 'connected' && '🚁 Дрон подключен к стриму'}
          {droneStatus === 'disconnected' && 'Дрон не подключен'}
        </div>
      )}

      <div className="video-container">
        {currentCall.type === 'video' && (
          <>
            <video ref={localVideoRef} autoPlay muted className="local-video" />
            <video ref={remoteVideoRef} autoPlay className="remote-video" />
          </>
        )}
      </div>

      <div className="call-controls">
        <button className="control-btn microphone" onClick={toggleMute}>
          <img src={isMuted ? "/icons/mute.png" : "/icons/unmute.png"} alt="microphone" className="icon-button" />
        </button>
        <button className="control-btn end-call" onClick={endCall}>
          <img src="/icons/phone.png" alt="end call" className="icon-button" />
        </button>
        <button className="control-btn camera">
          <img src="/icons/camera.png" alt="camera" className="icon-button" />
        </button>
      </div>
    </div>
  );

  // Рендер чата
  const renderChat = () => {
    const chatId = selectedChat.id;
    const messages = chatMessages[chatId] || [];
    
    return (
      <div className="chat-interface">
        <div className="chat-header">
          <button className="back-btn" onClick={() => setSelectedChat(null)}>←</button>
          <div className="chat-info">
            <div className="chat-avatar">{selectedChat.emoji || selectedChat.avatar || selectedChat.username[0].toUpperCase()}</div>
            <div>
              <h3>{selectedChat.username || selectedChat.name}</h3>
              <p>{selectedChat.character ? 'AI Агент онлайн' : 'В сети'}</p>
            </div>
          </div>
          <div className="chat-actions">
            {selectedChat.character ? (
              <>
                <button 
                  className="call-btn audio" 
                  onClick={() => startAICall("audio", selectedChat)}
                >
                  <img src="/icons/phone.png" alt="audio call" className="icon-button" />
                </button>
                <button 
                  className="call-btn video" 
                  onClick={() => startAICall("video", selectedChat)}
                >
                  <img src="/icons/camera.png" alt="video call" className="icon-button" />
                </button>
              </>
            ) : (
              <>
                <button 
                  className="call-btn audio" 
                  onClick={() => startCall("audio", selectedChat)}
                >
                  <img src="/icons/phone.png" alt="audio call" className="icon-button" />
                </button>
                <button 
                  className="call-btn video" 
                  onClick={() => startCall("video", selectedChat)}
                >
                  <img src="/icons/camera.png" alt="video call" className="icon-button" />
                </button>
              </>
            )}
          </div>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && selectedChat.character && (
            <div className="message received">
              <p>Привет! Я {selectedChat.name}. {selectedChat.description}. Как дела?</p>
              <span className="time">{new Date().toLocaleTimeString()}</span>
            </div>
          )}
          
          {messages.map(message => (
            <div 
              key={message.id} 
              className={`message ${message.role === 'user' ? 'sent' : 'received'} ${message.isError ? 'error' : ''}`}
            >
              <p>{message.text}</p>
              <span className="time">{new Date(message.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
          
          {isTyping && (
            <div className="message received typing">
              <p>Печатает...</p>
            </div>
          )}
        </div>

        <form className="chat-input" onSubmit={handleSendMessage}>
          <input 
            type="text" 
            placeholder="Напишите сообщение..." 
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            disabled={isTyping}
          />
          <button type="submit" disabled={isTyping || !currentMessage.trim()}>
            <img src="/icons/send.png" alt="send" className="icon-button" />
          </button>
        </form>
      </div>
    );
  };

  // Рендер списка чатов
  const renderChatsList = () => {
    // Объединяем реальных подключенных пользователей с тестовыми
    const allUsers = [...connectedUsers, ...testUsers];
    
    return (
      <div className="chats-list">
        {/* Поиск пользователей */}
        <div className="search-container">
          <div className="search-input-container">
            <input
              type="text"
              placeholder="Поиск пользователей по нику..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="search-input"
            />
            <div className="search-icon">🔍</div>
          </div>
          
          {/* Результаты поиска */}
          {searchQuery && (
            <div className="search-results">
              {isSearching ? (
                <div className="search-loading">Поиск...</div>
              ) : searchResults.length > 0 ? (
                searchResults.map(user => (
                  <div 
                    key={user.id} 
                    className="search-result-item" 
                    onClick={() => {
                      setSelectedChat(user);
                      setSearchQuery('');
                      setSearchResults([]);
                    }}
                  >
                    <div className="chat-avatar">
                      {user.username[0].toUpperCase()}
                    </div>
                    <div className="chat-content">
                      <h3>{user.username}</h3>
                      <p>Нажмите для начала чата</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="search-no-results">Пользователи не найдены</div>
              )}
            </div>
          )}
        </div>

        {/* Все пользователи (подключенные + тестовые) */}
        <div className="connected-users-section">
          <h3>Пользователи</h3>
          {allUsers.map(person => {
            const lastMessage = testMessages[person.id] ? testMessages[person.id][testMessages[person.id].length - 1] : null;
            return (
              <div 
                key={person.id} 
                className="chat-item" 
                onClick={() => {
                  setSelectedChat(person);
                  // Инициализируем сообщения для этого чата, если они есть
                  if (testMessages[person.id] && !chatMessages[person.id]) {
                    setChatMessages(prev => ({
                      ...prev,
                      [person.id]: testMessages[person.id]
                    }));
                  }
                }}
              >
                <div className="chat-avatar">
                  {person.avatar || person.username[0].toUpperCase()}
                  {person.is_online && <div className="online-indicator"></div>}
                </div>
                <div className="chat-content">
                  <div className="chat-header-info">
                    <h3>{person.username}</h3>
                    <span className="time">{new Date(person.last_seen).toLocaleTimeString()}</span>
                  </div>
                  <p>{lastMessage ? lastMessage.text : (person.is_online ? 'Онлайн' : 'Был(а) в сети')}</p>
                </div>
              </div>
            );
          })}
          {allUsers.length === 0 && !searchQuery && (
            <div className="no-users">
              <p>Нет подключенных пользователей</p>
              <p>Используйте поиск выше, чтобы найти пользователей</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Рендер списка AI агентов
  const renderAIAgentsList = () => (
    <div className="ai-agents-list">
      <div className="create-agent-button-container">
        <img src="/images/create_ai_agent_button.jpg" alt="Создать AI агента" className="create-agent-image-button" onClick={() => setShowCreateAgent(true)} />
      </div>
      
      {aiAgents.map(agent => (
        <div key={agent.id} className="ai-agent-card">
          <div className="agent-avatar">{agent.emoji}</div>
          <h3>{agent.name}</h3>
          <p>{agent.description}</p>
          <button 
            className="agent-chat-btn"
            onClick={() => setSelectedChat(agent)}
          >
            Нажмите для начала чата
          </button>
        </div>
      ))}
    </div>
  );

  // Рендер формы аутентификации
  if (!isAuthenticated) {
    return (
      <div className="auth-container">
        <div className="auth-form">
          <h1>Twinby</h1>
          <div className="auth-tabs">
            <button 
              className={authMode === 'login' ? 'active' : ''}
              onClick={() => setAuthMode('login')}
            >
              Вход
            </button>
            <button 
              className={authMode === 'register' ? 'active' : ''}
              onClick={() => setAuthMode('register')}
            >
              Регистрация
            </button>
          </div>

          <form onSubmit={handleAuthSubmit}>
            <input
              type="text"
              placeholder="Имя пользователя"
              value={authForm.username}
              onChange={(e) => setAuthForm({...authForm, username: e.target.value})}
              required
            />
            
            {authMode === 'register' && (
              <input
                type="email"
                placeholder="Email"
                value={authForm.email}
                onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                required
              />
            )}
            
            <input
              type="password"
              placeholder="Пароль"
              value={authForm.password}
              onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
              required
            />

            {authError && <div className="error">{authError}</div>}

            <button type="submit" disabled={authLoading}>
              {authLoading ? 'Загрузка...' : (authMode === 'login' ? 'Войти' : 'Зарегистрироваться')}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Основной рендер приложения
  if (isInCall) {
    return renderCallInterface();
  }

  if (showCreateAgent) {
    return renderCreateAgentForm();
  }

  if (selectedChat) {
    return renderChat();
  }

  return (
    <div className="app">
      <div className="app-header">
        <h1>{currentView === 'chats' ? 'Чаты' : 'AI Агенты'}</h1>
        <p>{currentView === 'chats' ? 'Ваши совпадения и беседы' : 'Выберите виртуального собеседника'}</p>
        <button onClick={handleLogout} className="logout-btn">Выйти ({currentUser?.username})</button>
      </div>

      <div className="navigation">
        <button 
          className={`nav-btn ${currentView === 'chats' ? 'active' : ''}`}
          onClick={() => setCurrentView('chats')}
        >
          Чаты
        </button>
        <button 
          className={`nav-btn ${currentView === 'ai' ? 'active' : ''}`}
          onClick={() => setCurrentView('ai')}
        >
          AI Агенты
        </button>
      </div>

      {incomingCall && (
        <div className="incoming-call-modal">
          <div className="modal-content">
            <h3>Входящий {incomingCall.type === 'video' ? 'видео' : 'аудио'}звонок</h3>
            <p>от {incomingCall.caller.username}</p>
            <div className="call-actions">
              <button 
                className="accept-btn"
                onClick={acceptCall}
              >
                Принять
              </button>
              <button 
                className="decline-btn"
                onClick={declineCall}
              >
                Отклонить
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="content">
        {currentView === 'chats' ? renderChatsList() : renderAIAgentsList()}
      </div>
    </div>
  );
};

export default App;



