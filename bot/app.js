require('dotenv').config();
const axios = require('axios');
const { Configuration, OpenAIApi } = require("openai");
const Discord = require('discord.js');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus } = require('@discordjs/voice');
const { formatWithOptions } = require('util');
const { execSync } = require('child_process');



// OpenAI client configuration
const configuration = new Configuration({ apiKey: process.env.OPENAI_API_KEY });
const openai = new OpenAIApi(configuration);

// Discord client configuration
const client = new Discord.Client({ intents: 131071 });



// Audio player and connection
const audioPlayer = createAudioPlayer();


// Get TTS audio
async function getAudio(textToSpeak) {
	console.log('Requesting WAV');

    try {
        const response = await axios.post(
			process.env.XTTS_ENDPOINT,
			{
				texttospeak: textToSpeak,
				voice: process.env.VOICE,
				voicefilter: process.env.VOICEFILTER
			},
			{
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${process.env.DPAAS_TOKEN}`
				},
				responseType: 'arraybuffer'
			}
		);
		require('fs').writeFileSync('./output.wav', response.data);
    } catch (error) {
        console.error('Error occurred while downloading the audio file:', error);
        throw error;
    }

	console.log('Audio file downloaded successfully.');
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
	const audioResource = createAudioResource('./output.wav');

	audio_filename = await getAudio(response)

	try {
		connection = joinVoiceChannel({
			channelId: voiceChannel.id,
			guildId: voiceChannel.guild.id,
			adapterCreator: voiceChannel.guild.voiceAdapterCreator,
		});
	
		audioPlayer.play(audioResource);
		connection.subscribe(audioPlayer);

		// Wait for the duration of the audio
		duration = 1000 * parseFloat(execSync(`ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 ${'./output.wav'}`));
		await new Promise(resolve => setTimeout(resolve, duration));

		// Reply by text so the other bot replies
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
		topic = message.content.substring("!reset".length).trim();
		messageHistory = [{role: "system", content: process.env.PREPROMPT}];
		messageHistory.push({role: "assistant", content: topic});
		if (process.env.INITIATEUR === "true") {
			await replyWithVoice(message, topic);
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