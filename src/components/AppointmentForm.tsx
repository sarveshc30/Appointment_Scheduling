import { useState } from "react";
import { format } from "date-fns";
import { CalendarIcon, Clock, User, Phone } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger } from
"@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"@/components/ui/select";
import { useToast } from "@/hooks/use-toast";

const timeSlots = [
"10:00 AM",
"11:00 AM",
"12:00 PM",
"1:00 PM",
"2:00 PM",
"3:00 PM"];


const AppointmentForm = () => {
  const API_BASE: string = import.meta.env.VITE_API_BASE_URL ?? "";
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [date, setDate] = useState<Date>();
  const [time, setTime] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const { toast } = useToast();

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name || !phone || !date || !time) {
      toast({
        title: "Missing fields",
        description: "Please fill in all fields.",
        variant: "destructive"
      });
      return;
    }

    setStatus("loading");

    try {
      const base = API_BASE.replace(/\/$/, "");
      const url = base ? `${base}/book-appointment` : "/book-appointment";

      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          phone,
          date: format(date, "yyyy-MM-dd"),
          time
        })
      });

      const result = await response.json();

      if (result.status === "success") {
        setStatus("success");
        toast({
          title: "✅ Appointment Booked!",
          description: `Your appointment on ${format(date, "PPP")} at ${time} is confirmed.`
        });
        setName("");
        setPhone("");
        setDate(undefined);
        setTime("");
        setTimeout(() => setStatus("idle"), 3000);
      } else {
        setStatus("error");
        toast({
          title: "Slot Unavailable",
          description: "This time slot is already taken. Please choose another.",
          variant: "destructive"
        });
        setTimeout(() => setStatus("idle"), 3000);
      }
    } catch {
      setStatus("error");
      toast({
        title: "Server Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive"
      });
      setTimeout(() => setStatus("idle"), 3000);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="w-full max-w-md">

      <div className="rounded-2xl bg-card p-8 md:p-10" style={{ boxShadow: "var(--shadow-card)" }}>
        <div className="mb-8 text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl"
            style={{ background: "var(--gradient-primary)" }}>

            <CalendarIcon className="h-7 w-7 text-primary-foreground" />
          </motion.div>
          <h2 className="text-2xl font-bold text-foreground font-sans">Book Your Appointment</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Choose a date and time that works best for you
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-sm font-medium text-foreground">
              Full Name
            </Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="name"
                placeholder="Enter your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="pl-10"
                required />

            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone" className="text-sm font-medium text-foreground">
              Phone Number
            </Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="phone"
                type="tel"
                placeholder="+91XXXXXXXXXX"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="pl-10"
                required />

            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium text-foreground">Select Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !date && "text-muted-foreground"
                  )}>

                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {date ? format(date, "PPP") : "Pick a date"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={setDate}
                  disabled={(d) => d < today}
                  initialFocus
                  className="p-3 pointer-events-auto" />

              </PopoverContent>
            </Popover>
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium text-foreground">Select Time</Label>
            <Select value={time} onValueChange={setTime}>
              <SelectTrigger className="w-full">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <SelectValue placeholder="Choose a time slot" />
                </div>
              </SelectTrigger>
              <SelectContent>
                {timeSlots.map((slot) =>
                <SelectItem key={slot} value={slot}>
                    {slot}
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={status}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}>

              <Button
                type="submit"
                disabled={status === "loading"}
                className="w-full h-12 text-base font-semibold text-primary-foreground"
                style={{ background: "var(--gradient-primary)" }}>

                {status === "loading" ?
                "Checking availability..." :
                status === "success" ?
                "✅ Booked Successfully!" :
                status === "error" ?
                "Try Again" :
                "Book Appointment"}
              </Button>
            </motion.div>
          </AnimatePresence>
        </form>
      </div>
    </motion.div>);

};

export default AppointmentForm;