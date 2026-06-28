import { Box, Loader } from '@mantine/core';

const TypingIndicator = () => {
  return (
    <Box
      sx={{
        alignSelf: 'flex-start',
        backgroundColor: '#FFF',
        padding: '10px 14px',
        borderRadius: '8px',
        margin: '4px 0',
        maxWidth: '80%',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <Loader variant="dots" color="gray" size="sm" />
    </Box>
  );
};

export default TypingIndicator;
