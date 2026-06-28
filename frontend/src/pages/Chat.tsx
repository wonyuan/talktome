import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  Flex,
  Grid,
  MantineProvider,
  Text,
  Textarea,
  useMantineTheme,
  Avatar
} from '@mantine/core';
import { IconSend, IconArrowLeft } from '@tabler/icons-react';
import ChatMessage from '@molecules/ChatMessage';
import TypingIndicator from '@molecules/TypingIndicator';
import { useNavigate, useLocation } from 'react-router-dom';
import { theme } from '@styles/theme';
import { profiles } from '@constants/personas';
import { fetchChat } from '@api/messages';
import { fetchEvaluation } from '@api/evaluation';
import { fetchScenario } from '@api/scenario';
import useRequest from "@hooks/useRequest";
import useLoading from "@context/loadingContext";
import Loader from "@atoms/Loader";

interface Message {
  text: string;
  isUser: boolean;
}

const Chat = () => {
  const m = useMantineTheme();
  const navigate = useNavigate();
  const { setLoading } = useLoading();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [scenario, setScenario] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const location = useLocation();
  const { persona, paragraph } = location.state || {}; 
  const classification = persona?.classification as keyof typeof profiles;
  const profile = profiles[classification];

  const chatHistory: Message[] = [];

  useEffect(() => {
    const fetchScenarioData = async () => {
      if (paragraph) {
        try {
          const data = await fetchScenario({ params: { situation: paragraph } });
          setScenario(data.profile_intro);
        } catch (error) {
          console.error("Error fetching scenario:", error);
        }
      }
    };

    fetchScenarioData();
  }, [paragraph]); 

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // EVALUATION ENDPOINT
  const { makeRequest } = useRequest({
    request: fetchEvaluation,
    requestByDefault: false,
  });

  const handleSubmit = async () => {
    setLoading(true);
    const response = await makeRequest({chat_history: messages, scenario});
    console.log("RESPONSE", response);

    setLoading(false);
    
    if (response) {
      navigate("/results", 
        { state: 
          { data: response, 
            situation: scenario,
            persona: persona
          } 
        });
    }
  };

  // Minimum time the typing bubble stays up, so replies feel natural even when
  // the API responds instantly.
  const MIN_TYPING_MS = 3000;

  const sendMessage = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage = input;
    const userMessageObj = { text: userMessage, isUser: true };

    chatHistory.push(userMessageObj);
    setMessages((prevMessages) => [...prevMessages, userMessageObj]);
    setInput('');
    setIsTyping(true);

    const params = {
      classification: persona.classification,
      situation: paragraph,
      user_input: userMessage,
      // chat_history: chatHistory,
    };

    try {
      const start = Date.now();
      const data = await fetchChat({ params });
      const botResponse = data?.bot_response || "Sorry, I couldn't get a response.";

      // Keep the typing bubble up for at least MIN_TYPING_MS total.
      const elapsed = Date.now() - start;
      if (elapsed < MIN_TYPING_MS) {
        await new Promise((resolve) => setTimeout(resolve, MIN_TYPING_MS - elapsed));
      }

      const botMessageObj = { text: botResponse, isUser: false };
      chatHistory.push(botMessageObj);
      setMessages((prevMessages) => [...prevMessages, botMessageObj]);

    } catch (error) {
      console.error('Error fetching chatbot response:', error);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <MantineProvider theme={theme}>
      <Loader />
      <Flex
        direction="column"
        justify="center"
        align="center"
        sx={{
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          height: '100vh',
          backgroundImage: `url('/bg.png')`,
        }}
      >
        <Flex direction="column" sx={{ position: 'relative', width: '900px', marginTop: '48px' }}>
          <Button
            variant="gradient"
            gradient={{ from: m.colors.moss[2], to: m.colors.moss[2], deg: 99 }}
            sx={{
              position: 'absolute',
              top: '-48px',
              zIndex: 10,
            }}
            onClick={() => navigate('/onboarding')}
          >
            <IconArrowLeft size={20} />
            <Text sx={{ fontSize: '12px', marginLeft: '8px' }} fw={600}>
              back
            </Text>
          </Button>

          <Grid gutter="md">
            <Grid.Col span={3}>
              <Box
                sx={{
                  height: '80vh',
                  backgroundColor: m.colors.snow[1],
                  borderRadius: '10px',
                  padding: '24px',
                  boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.1)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'left',
                  justifyContent: 'space-between',
                }}
              >
                <Text fw={700} sx={{ fontSize: '20px', color: m.colors.ebony[3], marginBottom: '16px' }}>
                  {profile.name}
                </Text>
                <Avatar color="blue" radius="sm" size={160} src={profile.headshot} sx={{ marginBottom: "24px" }} />
                <Text fw={700} sx={{ fontSize: '14px', color: m.colors.ebony[3] }}>
                  so here's the sketch... 
                </Text>
                <Text sx={{ fontSize: '10px', color: m.colors.ebony[3], marginBottom: "42px" }}>
                  {scenario}
                </Text>
                <Button
                  onClick={handleSubmit}
                  variant="gradient"
                  gradient={{ from: m.colors.snow[2], to: m.colors.snow[4], deg: 12 }}
                  sx = {{ marginBottom: "8px" }}
                >
                  i'm done
                </Button>
              </Box>
            </Grid.Col>

            <Grid.Col span={9}>
              <Box
                sx={{
                  height: '80vh',
                  backgroundColor: m.colors.snow[3],
                  borderRadius: '10px',
                  padding: '32px',
                  boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.2)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box
                  sx={{
                    flexGrow: 1,
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <Text><i>{profile.name} is ready to speak... try to figure out whats going on with him.</i></Text>
                  {messages.map((msg, index) => (
                    <ChatMessage key={index} text={msg.text} isUser={msg.isUser} />
                  ))}
                  {isTyping && <TypingIndicator />}
                  <div ref={messagesEndRef} />
                </Box>

                <Flex gap="sm" mt="24px">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.currentTarget.value)}
                    placeholder="Type your message..."
                    autosize
                    minRows={1}
                    sx={{ flexGrow: 1 }}
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={isTyping}
                    variant="gradient"
                    gradient={{ from: m.colors.ebony[1], to: m.colors.eerie[1], deg: 45 }}
                  >
                    <IconSend size={20} />
                  </Button>
                </Flex>
              </Box>
            </Grid.Col>
          </Grid>
        </Flex>
      </Flex>
    </MantineProvider>
  );
};

export default Chat;
