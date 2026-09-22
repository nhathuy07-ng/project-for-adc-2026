# User flow

0. Welcomes the user. Ask them basic pref questions:
    1. *"Are you planning to create a CV, or a portfolio?"* -> "<CV|Portfolio>, got it."
    2. *"Would you like to build your CV step-by-step through a guided voice interview, or simply speak out your raw notes for me to structure and polish?"*

--> Saves this to `PROFILE_TYPE` and `INTERACTION_MODE`

## CV creation (guided voice interview)

### Questions:
1. Basic info: "Tell me your full name, location, contact details, and the job title you're targeting."

2. Profile links: "Do you have a LinkedIn handle, GitHub username, portfolio link or other profiles you’d like to include?"

3. Professional summary: "How would you introduce yourself professionally in two or three sentences, and what are your main strengths?"

4. Experience: "Walk me through your relevant past experiences — this can include traditional jobs, freelance work, side gigs, or community volunteering. What was the role, where and when was it, and what did you achieve?"

5. Skills and Tools: "What tools, technologies, software, or domain expertise do you use most often in your day-to-day work?"

6. Projects & Certifications: "Are there any standout projects, licenses, or certifications you’d like to highlight?"

### Reconfirmation (not in 1st proto.)

1. After each question, read back what the model plans to write into the CV. Ask the user, "Did I get the details right, or do you want to make any changes?".

2. After all questions, prompts if it needs to re-read the entire CV and allow any amendments as needed. Re-read one last time after the amendment is done.

### Interruptible voice-line

3. Allow voice-line to be interruptible (using F or J keys), and allow for jumping back and forth (e.g "Wait, I want to change something in <part>.", or "By the way, ...").

### Export

1. Describe CV style (focusing on layout).
1. Currently, only two CV style.

## CV creation (raw notes)

1. User input raw notes.
2. AI asks to clarify if any
3. When done, AI reads back the portfolio.
4. User makes amendment.
5. System reads back what's changed.
6. Loop until user's statisfied. If nothing changes, system will ask if it needs reading back once more.

## Portfolio creation: Later on
