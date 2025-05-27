import { ExpandableChatDemo } from "@/components/expandable-chat-demo"

export default function Home() {
  return (
    <div
      className="min-h-screen bg-cover bg-center bg-no-repeat"
      style={{
        backgroundImage: "url('/bg.png')",
      }}
    >
      {/* Expandable Chat Component */}
      <ExpandableChatDemo />
    </div>
  )
}
