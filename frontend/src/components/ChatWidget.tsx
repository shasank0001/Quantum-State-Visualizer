import React, { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { X, Send, MessageCircle } from 'lucide-react';

interface Message { role: 'user' | 'assistant'; content: string }

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ChatWidget: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hi! I can help with circuits, QASM, and routing. Ask me anything.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [open, messages.length]);

  const send = async () => {
    const content = input.trim();
    if (!content) return;
    setInput('');
  const next: Message[] = [...messages, { role: 'user', content } as Message];
  setMessages(next as Message[]);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: next }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt);
      }
      const data = await res.json();
  setMessages((m) => [...m, { role: 'assistant', content: data.reply } as Message]);
    } catch (e: any) {
  setMessages((m) => [...m, { role: 'assistant', content: `Chat error: ${e.message || e}` } as Message]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-5 right-5 z-50">
        <Button className="rounded-full h-12 w-12 shadow-lg" onClick={() => setOpen((o) => !o)}>
          {open ? <X className="w-5 h-5" /> : <MessageCircle className="w-5 h-5" />}
        </Button>
      </div>

      {/* Chat Panel */}
      {open && (
        <div className="fixed bottom-20 right-5 z-50 w-[340px] sm:w-[380px]">
          <Card className="bg-background border-border shadow-xl rounded-xl overflow-hidden">
            <div className="flex items-center justify-between p-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Badge variant="secondary">Beta</Badge>
                <span className="font-medium">Assistant</span>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setOpen(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div ref={bodyRef} className="max-h-[360px] overflow-y-auto p-3 space-y-3">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`px-3 py-2 rounded-lg max-w-[80%] whitespace-pre-wrap text-sm ${
                    m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                  }`}>
                    {m.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="text-xs text-muted-foreground">Thinking…</div>
              )}
            </div>

            <div className="p-3 border-t border-border">
              <div className="flex items-end gap-2">
                <Textarea
                  placeholder="Ask about QASM, circuits, routing…"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="h-10 resize-none"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                />
                <Button onClick={send} disabled={loading} className="shrink-0">
                  <Send className="w-4 h-4 mr-1" />
                  Send
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </>
  );
};

export default ChatWidget;
