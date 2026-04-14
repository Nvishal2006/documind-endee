export async function fetchSSE(url, options, onMessage) {
    const response = await fetch(url, options);
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const dataStr = line.replace('data: ', '').trim();
                if (dataStr) {
                    try {
                        const data = JSON.parse(dataStr);
                        onMessage(data);
                    } catch (e) {
                        console.error('Error parsing SSE json', e, dataStr);
                    }
                }
            }
        }
    }
}
