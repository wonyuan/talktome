import { theme } from "@styles/theme.ts";
import { IconArrowLeft, IconRepeat, IconThumbUp, IconBulb, IconHeart, IconMessageCircle } from '@tabler/icons-react';
import { Box, Text, Button, Flex, MantineProvider, Avatar, useMantineTheme } from '@mantine/core';
import { useLocation, useNavigate } from 'react-router-dom';
import { profiles } from '@constants/personas';

const Results = () => {
    const m = useMantineTheme();
    const location = useLocation();
    const navigate = useNavigate();

    const { data, situation, persona } = location.state || {}; 
    const classification = persona?.classification as keyof typeof profiles;
    const profile = profiles[classification];

    return (
      <MantineProvider theme={theme}>
        <Flex           
            direction="column"
            justify="center"
            align="center"
            sx={{ 
                backgroundSize: "cover",
                backgroundPosition: "center",
                backgroundRepeat: "no-repeat",
                height: "100vh",
                backgroundImage:`url('/bg.png')`,
            }}
        >
            <Flex
                direction="column"
                sx={{
                    position: "relative",
                    width: "900px",
                    marginTop: "40px",
                }}
            >
                <Flex direction="row" gap="10px" align="center" sx={{ marginBottom: "12px", marginTop: "-52px" }}>
                    <Button
                        variant="gradient"
                        gradient={{ from: m.colors.moss[2], to: m.colors.moss[2], deg: 99 }}
                        sx={{ zIndex: 10 }}
                        onClick={() => navigate('/')}
                    >
                        <IconArrowLeft size={20} />
                        <Text sx={{ fontSize: "12px", marginLeft: "8px" }} fw={600}>
                            home
                        </Text>
                    </Button>
                    <Button
                        variant="gradient"
                        onClick={() => navigate('/onboarding')}
                        gradient={{ from: m.colors.snow[2], to: m.colors.snow[2], deg: 99 }}
                        sx={{ zIndex: 10 }}
                    >
                        <IconRepeat size={20} />
                        <Text sx={{ fontSize: "12px", marginLeft: "8px" }} fw={600}>
                            new prompt
                        </Text>
                    </Button>
                </Flex>

                <Box
                    sx={{
                        width: "100%",
                        maxHeight: "80vh",
                        overflowY: "auto",
                        backgroundColor: m.colors.snow[3],
                        borderRadius: "10px",
                        padding: "48px",
                        boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
                        display: "flex",
                        flexDirection: "column",
                    }}
                >
                    <Box sx={{           
                        backgroundColor: '#EFC9B1',
                        borderRadius: '10px',
                        padding: '10px 10px 10px 20px',
                        height: '120px',
                        boxShadow: "0px 4px 5px rgba(0, 0, 0, 0.05)",
                        display: "flex",
                        alignItems: "center",
                        marginBottom: "20px",
                    }}>
                        <Avatar size={80} src={profile?.headshot}/>
                        <Flex direction="column">
                            <Text sx={{ fontSize: "16px", color: m.colors.snow[4], marginLeft: "20px" }} fw={700}>
                                {profile?.name}...
                            </Text>
                            <Text sx={{ fontSize: "14px", color: m.colors.snow[4], marginLeft: "20px" }} fw={400}>
                                can sense your willingness and warmth as a parent.
                            </Text>
                        </Flex>
                    </Box>

                    <Text sx={{ fontSize: "14px", color: m.colors.ebony[4] }} fw={500}>
                        Firstly, it's important to know that you <i>are</i> doing your best. You're never alone in your journey through parenthood, 
                        and every step you take is a step in the right direction...
                    </Text>
                    <Text sx={{ fontSize: "16px", color: m.colors.ebony[4] }} fw={700}> 
                        and finally, we've gathered some insights to help you navigate similar situations in the future:
                    </Text>

                    <Box sx={{ marginTop: "24px" }}>
                        {data?.Output && Object.entries(data.Output).map(([category, message]) => {
                            const iconFor = (name: string) => {
                                const n = name.toLowerCase();
                                if (n.includes("well")) return <IconThumbUp size={18} />;
                                if (n.includes("improve")) return <IconBulb size={18} />;
                                if (n.includes("connect") || n.includes("advice")) return <IconHeart size={18} />;
                                return <IconMessageCircle size={18} />;
                            };
                            return (
                                <Box
                                    key={category}
                                    sx={{
                                        backgroundColor: m.colors.snow[0],
                                        borderRadius: "10px",
                                        borderLeft: `4px solid ${m.colors.snow[4]}`,
                                        padding: "16px 20px",
                                        marginBottom: "16px",
                                        boxShadow: "0px 2px 5px rgba(0, 0, 0, 0.05)",
                                    }}
                                >
                                    <Flex align="center" gap="8px" sx={{ marginBottom: "8px", color: m.colors.snow[4] }}>
                                        {iconFor(category)}
                                        <Text sx={{ fontSize: "15px", fontWeight: 700, color: m.colors.snow[4] }}>
                                            {category}
                                        </Text>
                                    </Flex>
                                    <Text sx={{ fontSize: "13px", lineHeight: 1.6, color: m.colors.ebony[4] }}>
                                        {message as string}
                                    </Text>
                                </Box>
                            );
                        })}
                    </Box>
                </Box>
            </Flex>
        </Flex>
      </MantineProvider>
    );
};

export default Results;
