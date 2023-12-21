require('dotenv').config();
const axios = require('axios');
const { Configuration, OpenAIApi } = require("openai");
const Discord = require('discord.js');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus } = require('@discordjs/voice');
const { formatWithOptions } = require('util');




// OpenAI client configuration
const configuration = new Configuration({ apiKey: process.env.OPENAI_API_KEY });
const openai = new OpenAIApi(configuration);

// Discord client configuration
const client = new Discord.Client({ intents: 131071 });



// Audio player and connection
const audioPlayer = createAudioPlayer();


// Get TTS audio
async function getAudio(textToSpeak) {
    const url = `http://${process.env.XTTS_HOST}:${process.env.XTTS_PORT}/generate`;

	console.log('Requesting WAV');

    try {
        const response = await axios.post(
			url,
			{ text: textToSpeak, voice: process.env.VOICE },
			{ headers: { 'Content-Type': 'application/json', 'Authorization': process.env.XTTS_TOKEN }, responseType: 'arraybuffer' }
		);

        // Save the response as an WAV file
        const filePath = './output.wav';
		require('fs').writeFileSync(filePath, response.data);

        console.log('Audio file downloaded successfully.');
        return filePath;
    } catch (error) {
        console.error('Error occurred while downloading the audio file:', error);
        throw error;
    }
}


// Message history
let messageHistory = [{role: "system", content: process.env.PREPROMPT}];


// Respond to prompts
async function runCompletion(gptprompt) {
	messageHistory.push({role: "user", content: gptprompt});

	try {
		const response = await openai.createChatCompletion({
			model: "gpt-3.5-turbo",
			messages: messageHistory,
		});

		// Save AI answer to the message history
		messageHistory.push(response.data.choices[0].message);

		return response.data.choices[0].message.content;
	} catch (error) {
		console.log('Error occurred:');
		console.error(error);
  
		// Handle specific error scenarios
		if (error.response) {
			console.log('API response status:');
			console.log(error.response.status);
			console.log('API response data:');
			console.log(error.response.data);
		}

		return null;
	}
}


// Reply by voice chat
async function replyWithVoice(message, response)
{
	const voiceChannel = message.member?.voice.channel;
	const audioPath = await getAudio(response)
	const audioResource = createAudioResource(audioPath);

	try {
		connection = joinVoiceChannel({
			channelId: voiceChannel.id,
			guildId: voiceChannel.guild.id,
			adapterCreator: voiceChannel.guild.voiceAdapterCreator,
		});
	
		audioPlayer.play(audioResource);
		connection.subscribe(audioPlayer);
		await new Promise(resolve => setTimeout(resolve, 20000));
		message.channel.send(response);
	} catch (error) {
		console.error('Error occurred while playing audio:', error);
		message.channel.send("An error occurred while playing audio.");
	}
}



// Set up Discord bot events
client.on('ready', () => {
	console.log(`Logged in as ${client.user.tag}!`);
});

client.on('interactionCreate', interaction => {
	console.log(interaction);
});

client.on("messageCreate", async message => {
	console.log(`Received message`);

	// Ignore messages from the bot itself
	if (message.author.id === client.user.id) {
		console.log('Message was from myself. Ignoring');
		return;
	}

	// Handle ping
	else if (message.content.startsWith("ping")) {
		console.log('Message is a ping request. Ignoring');
		message.channel.send("pong");
	}

	// Handle resets
	else if (message.content.startsWith("!reset")) {
		console.log('Restarting the bot.');
		audioPlayerStatus = "idle"
		messageHistory = [{role: "system", content: process.env.PREPROMPT}];
		if (process.env.INITIATEUR === "true")
		{
			await replyWithVoice(message, process.env.INITIATEUR_MESSAGE);
		}
	}

	// Otherwise, send to ChatGPT
	else {
		console.log('Replying using ChatGPT');

		const prompt = message.content;
		const response = await runCompletion(prompt);
		console.log('Got ChatGPT completion. Replying');

		// The user is in a voice channel
		if (message.member?.voice.channel) {
			await replyWithVoice(message, response);
		}

		// Send text
		else {
			message.channel.send(response);
		}
	}
});


// Log into Discord
client.login(process.env.DISCORD_API_KEY);