let canvas;
let context;

let fpsInterval = 1000 / 60;
let then = Date.now();

let startTime = null;
let elapsedTime = 0;
let timerStarted = false;

let request;

let moveLeft = false;
let moveUp = false;
let moveRight = false;
let moveDown = false;


let p = {
    x : 490,
    y : 255,
    size : 20,
    xChange : 5,
    yChange : 5
}

const maxPlayerHp = 10;
let playerHp = maxPlayerHp;
let PlayerInvincibility = 0;
let playerBullets = [];

let enemyTypes = {
    walker: {
        speed:8,
        size: 40,
        damage: 1,
        moveLimit: 100,
        waitDuration: 30
    },
    seeker: {
        speed: 3.5,
        size: 40,
        damage: 1
    },
    shooter: {
        speed: 0,
        size: 40,
        damage: 1,
        shootCooldown: 60
    },
    tank: {
        speed: 1,
        size: 70,
        damage: 3
    }
}


// I did the graphics of the enemies with the help of this web page:
//https://spicyyoghurt.com/tutorials/html5-javascript-game-development/images-and-sprite-animations
// every graphic of a enemy is free from itch.io
let enemySprites = {
    walker: new Image(),
    seeker: new Image(),
    shooter: new Image(),
    tank: new Image()
}

enemySprites.walker.src = "static/AntleredRascal.png";
enemySprites.seeker.src = "static/CrimsonImp.png";
enemySprites.shooter.src = "static/FloatingEye.png";
enemySprites.tank.src = "static/PitBalor.png";

let walls = [];
let chests = [];
let gates = [];

let rooms = {
    "north_0": {
        background: new Image(),
        doors: { top: false, bottom: true, left: false, right: false },
        gates: { top: false, bottom: false, left: false, right: false },
        chests: false, 
        cleared: true,
        enemies: [
            
        ]
    },
    "center_1": {
        background: new Image(),
        doors: { top: true, bottom: true, left: true, right: true },
        gates: { top: true, bottom: true, left: true, right: true },
        chests: true, 
        cleared: false,
        enemies: [
            { type: "walker", count: 2 },
            { type: "seeker", count: 1 }
        ]
    },
    "west_2": {
        background: new Image(),
        doors: { top: false, bottom: false, left: false, right: true },
        gates: { top: false, bottom: false, left: false, right: true },
        chests: true, 
        cleared: false,
        enemies: [
            { type: "seeker", count: 2 },
            { type: "shooter", count: 1 }
        ]
    },
    "east_3": {
        background: new Image(),
        doors: { top: false, bottom: false, left: true, right: false },
        gates: { top: false, bottom: false, left: true, right: false },
        chests: true, 
        cleared: false,
        enemies: [
            { type: "walker", count: 4 },
            { type: "tank", count: 1 }
        ]
    },
    "south_4": {
        background: new Image(),
        doors: { top: true, bottom: false, left: false, right: false },
        gates: { top: true, bottom: false, left: false, right: false },
        chests: true, 
        cleared: false,
        enemies: [
            { type: "tank", count: 1 },
            { type: "shooter", count: 3 }
        ]
    }
    
};

let currentRoomKey = "north_0";

// images created with AI, with https://deepai.org/machine-learning-model/text2img
// the prompt that was used:
//i want you to create a background for a  2D game with the number "Number" in the 
//middle. make the number really small. use a  rocky feeling.
//make little arrow that points "Direction"

rooms["center_1"].background.src = "static/oneMap.jpg";
rooms["north_0"].background.src = "static/zeroMap.jpg";
rooms["south_4"].background.src = "static/fourMap.jpg";
rooms["west_2"].background.src = "static/twoMap.jpg";
rooms["east_3"].background.src = "static/threeMap.jpg";

let chestSprite = new Image();
chestSprite.src = "static/chest.png";




//building and transitioning between the rooms..................................................................


function buildRoom() {
    const room = rooms[currentRoomKey];
    const W = canvas.width;
    const H = canvas.height;
    const thickness = 10; 
    const doorSize = 50;  
    
    walls = [];
    chests = [];
    gates = [];

    function addWall(x, y, w, h) {
        walls.push({ x: x, y: y, width: w, height: h });
    }
    function addGate(x, y, w, h){
        gates.push({ x: x, y: y, width: w, height: h });
    }
    
    if (room.doors.top) {
        addWall(0, 0, (W - doorSize) / 2, thickness);
        addWall((W + doorSize) / 2, 0, (W - doorSize) / 2, thickness);
    } else {
        addWall(0, 0, W, thickness);
    }

    if (room.doors.bottom) {
        addWall(0, H - thickness, (W - doorSize) / 2, thickness);
        addWall((W + doorSize) / 2, H - thickness, (W - doorSize) / 2, thickness);
    } else {
        addWall(0, H - thickness, W, thickness);
    }

    if (room.doors.left) {
        addWall(0, 0, thickness, (H - doorSize) / 2);
        addWall(0, (H + doorSize) / 2, thickness, (H - doorSize) / 2);
    } else {
        addWall(0, 0, thickness, H);
    }

    if (room.doors.right) {
        addWall(W - thickness, 0, thickness, (H - doorSize) / 2);
        addWall(W - thickness, (H + doorSize) / 2, thickness, (H - doorSize) / 2);
    } else {
        addWall(W - thickness, 0, thickness, H);
    }


    if (room.chests){
        chests.push({x: 470, y: 250, width: 60, height: 60})
    }


    if (room.gates.top){
        addGate(475,0,50,10);
    }
    if (room.gates.bottom){
        addGate(475,590,50,10);
    }
    if (room.gates.left){
        addGate(0,275,10,50);
    }
    if (room.gates.right){
        addGate(990,275,10,50);
    }

    if (!room.cleared){
        spawnEnemies();
    }
}

function checkRoomTransition() {
    const W = canvas.width;
    const H = canvas.height;

    if (p.x > W) { //exit to right
        if (currentRoomKey === "center_1"){
            currentRoomKey = "east_3"
        } 
        else if (currentRoomKey === "west_2"){
            currentRoomKey = "center_1"
        } 
        p.x = 10; 
        buildRoom();
    }
    else if (p.x + p.size < 0) {//exit to left
        if (currentRoomKey === "center_1"){
            currentRoomKey = "west_2"
        } 
        else if (currentRoomKey === "east_3"){
            currentRoomKey = "center_1"
        } 
        p.x = W - p.size - 10; 
        buildRoom();
    }
    else if (p.y + p.size < 0) {// exit to top
        if (currentRoomKey === "center_1"){
            currentRoomKey = "north_0"
        } 
        else if (currentRoomKey === "south_4"){
            currentRoomKey = "center_1"
        } 
        p.y = H - p.size - 10; 
        buildRoom();
    }
    else if (p.y > H) {// exit to bottom
        if (currentRoomKey === "center_1"){
            currentRoomKey = "south_4"
        } 
        else if (currentRoomKey === "north_0"){
            currentRoomKey = "center_1"
        } 
        p.y = 10; 
        buildRoom();
    }

    if (!timerStarted && currentRoomKey === "center_1") {
        timerStarted = true;
        startTime = Date.now();
    }

}

// things about player and shooting....................................................................
//used for hp and bullets: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/splice#:~:text=The%20splice()%20method%20of,original%20array%2C%20use%20toSpliced()%20

function updatePlayerBullets() {
    for (let i = playerBullets.length - 1; i >= 0; i--) {
        playerBullets[i].x += playerBullets[i].dx;
        playerBullets[i].y += playerBullets[i].dy;

        if (playerBullets[i].x < 0 || playerBullets[i].x > 1000 ||
            playerBullets[i].y < 0 || playerBullets[i].y > 600) {
            playerBullets.splice(i, 1);
            continue;
        }

        for (let j = enemies.length - 1; j >= 0; j--) {
            if (is_colliding(playerBullets[i], enemies[j])) {
                enemies[j].hp = (enemies[j].hp) - 1;
                if (enemies[j].hp <= 0) {
                    enemies.splice(j, 1);
                }
                playerBullets.splice(i, 1);
                break;
            }
        }
    }
}

function drawPlayerBullets() {
    context.fillStyle = "white";
    for (let bullet of playerBullets) {
        context.beginPath();
        context.arc(bullet.x, bullet.y, bullet.size, 0, Math.PI * 2);
        context.fill();
    }
}

function drawPlayerHealth() {
    const barWidth = 200;
    const barHeight = 14;
    const x = canvas.width - barWidth - 15;
    const y = 30;

    const hp = Math.max(0, Math.min(maxPlayerHp, playerHp));
    const ratio = hp / maxPlayerHp;

    context.save();
    context.fillStyle = "rgba(0,0,0,0.6)";
    context.fillRect(x - 2, y - 2, barWidth + 4, barHeight + 4);
    context.fillStyle = "gray";
    context.fillRect(x, y, barWidth, barHeight);
    context.fillStyle = ratio > 0.5 ? "green" : ratio > 0.25 ? "orange" : "red";
    context.fillRect(x, y, barWidth * ratio, barHeight);

    context.fillStyle = "white";
    context.font = "12px Arial";
    context.textAlign = "right";
    context.textBaseline = "bottom";
    context.fillText(`HP ${hp}/${maxPlayerHp}`, x + barWidth, y - 4);
    context.restore();
}

// things about enemies...............................................................................
let enemies = [];

const enemyHP = {
    walker: 2,
    seeker: 3,
    shooter: 4,
    tank: 8
};

function spawnEnemies() {
    enemies = [];
    const room = rooms[currentRoomKey];

    for (let group of room.enemies) {
        let type = enemyTypes[group.type];

        for (let i = 0; i < group.count; i++) {
            const maxHp = enemyHP[group.type] ?? 3;
            let enemy = {
                type: group.type,
                x: 100 + Math.random() * 800,
                y: 100 + Math.random() * 400,
                size: type.size,
                speed: type.speed,
                color: type.color,
                damage: type.damage,

                hp: maxHp,
                maxHp: maxHp,

                dx: 0,
                dy: 0,
                distanceMoved: 0,
                moveLimit: type.moveLimit || 0,
                waiting: false,
                waitTimer: 0,
                waitDuration: type.waitDuration || 0,

                shootTimer: 0,
                shootCooldown: type.shootCooldown || 0,
            };

            if (group.type === "walker") {
                pickEnemyDirection(enemy);
            }

            enemies.push(enemy);
        }
    }
}

let bullets = [];
function updateEnemies() {
    for (let enemy of enemies) {
        if (enemy.type === "walker") updateWalker(enemy);
        if (enemy.type === "seeker") updateSeeker(enemy);
        if (enemy.type === "shooter") updateShooter(enemy);
        if (enemy.type === "tank") updateTank(enemy);
    }
}

function drawEnemies() {
    for (let enemy of enemies) {
        //for the graphics of the enemies:
        //https://spicyyoghurt.com/tutorials/html5-javascript-game-development/images-and-sprite-animations
        context.drawImage(
            enemySprites[enemy.type],
            0, 0,
            16, 16,
            enemy.x, enemy.y,
            enemy.size, enemy.size
        );

        
        const barWidth = enemy.size;
        const barHeight = 6;
        const barX = enemy.x;
        const barY = enemy.y - 10;
        const maxHp = Math.max(1, enemy.maxHp || 1);
        const hp = Math.max(0, Math.min(maxHp, enemy.hp ?? maxHp));
        const ratio = hp / maxHp;

        context.fillStyle = "rgba(0,0,0,0.6)";
        context.fillRect(barX - 1, barY - 1, barWidth + 2, barHeight + 2);
        context.fillStyle = "gray";
        context.fillRect(barX, barY, barWidth, barHeight);
        context.fillStyle = ratio > 0.5 ? "green" : ratio > 0.25 ? "orange" : "red";
        context.fillRect(barX, barY, barWidth * ratio, barHeight);

        context.fillStyle = "white";
        context.font = "10px Arial";
        context.textAlign = "center";
        context.textBaseline = "bottom";
        context.fillText(String(hp), enemy.x + enemy.size / 2, barY - 1);
    }
}

function pickEnemyDirection(enemy) {
    const directions = [
        { dx: 1, dy: 0 }, { dx: -1, dy: 0 },
        { dx: 0, dy: 1 }, { dx: 0, dy: -1 }
    ];
    const chosen = directions[Math.floor(Math.random() * directions.length)];
    enemy.dx = chosen.dx;
    enemy.dy = chosen.dy;
}

function updateWalker(enemy) {
    if (enemy.waiting) {
        enemy.waitTimer++;
        if (enemy.waitTimer >= enemy.waitDuration) {
            enemy.waiting = false;
            enemy.waitTimer = 0;
            pickEnemyDirection(enemy);
        }
    } else {
        enemy.x += enemy.dx * enemy.speed;
        enemy.y += enemy.dy * enemy.speed;
        enemy.distanceMoved += enemy.speed;

        enemy.x = Math.max(10 + enemy.size, Math.min(990 - enemy.size, enemy.x));
        enemy.y = Math.max(10 + enemy.size, Math.min(590 - enemy.size, enemy.y));

        if (enemy.distanceMoved >= enemy.moveLimit) {
            enemy.distanceMoved = 0;
            enemy.waiting = true;
        }
    }
}

function updateSeeker(enemy) {
    let dx = p.x - enemy.x;
    let dy = p.y - enemy.y;
    let dist = Math.sqrt(dx * dx + dy * dy);
    enemy.x += (dx / dist) * enemy.speed;
    enemy.y += (dy / dist) * enemy.speed;
}

function updateShooter(enemy) {
    enemy.shootTimer++;
    if (enemy.shootTimer >= enemy.shootCooldown) {
        enemy.shootTimer = 0;
        spawnBullet(enemy);
    }
}

function spawnBullet(enemy) {
    let dx = p.x - enemy.x;
    let dy = p.y - enemy.y;
    let dist = Math.sqrt(dx * dx + dy * dy);
    bullets.push({
        x: enemy.x,
        y: enemy.y,
        dx: (dx / dist) * 4,
        dy: (dy / dist) * 4,
        size: 6
    });
}

function updateBullets() {
    for (let i = bullets.length - 1; i >= 0; i--) {
        bullets[i].x += bullets[i].dx;
        bullets[i].y += bullets[i].dy;

        if (PlayerInvincibility === 0 && is_colliding(bullets[i], p)) {
            playerHp -= 1;
            PlayerInvincibility = 30;
            bullets.splice(i, 1);

            if (playerHp <= 0) {
                stop(2);
                return;
            }
            continue;
        }

        if (bullets[i].x < 0 || bullets[i].x > 1000 ||
            bullets[i].y < 0 || bullets[i].y > 600) {
            bullets.splice(i, 1);
        }
    }
}

function drawBullets() {
    context.fillStyle = "yellow";
    for (let bullet of bullets) {
        context.beginPath();
        context.arc(bullet.x, bullet.y, bullet.size, 0, Math.PI * 2);
        context.fill();
    }
}

function updateTank(enemy) {
    let dx = p.x - enemy.x;
    let dy = p.y - enemy.y;
    let dist = Math.sqrt(dx * dx + dy * dy);
    enemy.x += (dx / dist) * enemy.speed;
    enemy.y += (dy / dist) * enemy.speed;
}






document.addEventListener("DOMContentLoaded", init, false);
function init() {
    canvas = document.querySelector("canvas");
    context = canvas.getContext("2d");

    window.addEventListener("keydown", activate, false);
    window.addEventListener("keyup", deactivate, false);
    canvas.addEventListener("mousedown", shootBullet, false);

    buildRoom();
    draw();
}

function draw() {
    request = window.requestAnimationFrame(draw);
    let now = Date.now();
    let elapsed = now - then;
    if (elapsed <= fpsInterval){
        return;
    }
    then = now - (elapsed % fpsInterval);

    if (timerStarted) {
        elapsedTime = Date.now() - startTime;
    }

    context.clearRect(0, 0, canvas.width, canvas.height);

    if (PlayerInvincibility > 0){
        PlayerInvincibility--;
    } 

    // drawImage function from: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/drawImage
    // Fix for the transparency of the images: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/globalAlpha
    context.globalAlpha = 0.5; 
    context.drawImage(rooms[currentRoomKey].background, 0, 0, canvas.width, canvas.height);
    context.globalAlpha = 1;   

    let canMoveRight = true;
    let canMoveLeft = true;
    let canMoveUp = true;
    let canMoveDown = true;

    for (let wall of walls) {
        if (is_colliding({x: p.x + p.xChange, y: p.y, size: p.size}, wall)) canMoveRight = false;
        if (is_colliding({x: p.x - p.xChange, y: p.y, size: p.size}, wall)) canMoveLeft = false;
        if (is_colliding({x: p.x, y: p.y - p.yChange, size: p.size}, wall)) canMoveUp = false;
        if (is_colliding({x: p.x, y: p.y + p.yChange, size: p.size}, wall)) canMoveDown = false;
    }
    
    for (let gate of gates) {
        if (is_colliding({x: p.x + p.xChange, y: p.y, size: p.size}, gate)) canMoveRight = false;
        if (is_colliding({x: p.x - p.xChange, y: p.y, size: p.size}, gate)) canMoveLeft = false;
        if (is_colliding({x: p.x, y: p.y - p.yChange, size: p.size}, gate)) canMoveUp = false;
        if (is_colliding({x: p.x, y: p.y + p.yChange, size: p.size}, gate)) canMoveDown = false;
    }

    const room = rooms[currentRoomKey];
    if (room.cleared){
        for (let ch of chests){

            context.drawImage(
                chestSprite,
                96, 0,
                48, 32,
                ch.x, ch.y,
                ch.width, ch.height
            );
            
            if (is_colliding({x: p.x + p.xChange, y: p.y, size: p.size}, ch) ||
                is_colliding({x: p.x - p.xChange, y: p.y, size: p.size}, ch) ||
                is_colliding({x: p.x, y: p.y - p.yChange, size: p.size}, ch) ||
                is_colliding({x: p.x, y: p.y + p.yChange, size: p.size}, ch)) {

                if(currentRoomKey === "center_1"){
                    room.gates.top =  false;
                    room.gates.left = false;
                }
                if(currentRoomKey === "west_2"){
                    room.gates.right = false;
                    rooms["center_1"].gates.right = false;
                }
                if(currentRoomKey === "east_3"){
                    room.gates.left = false;
                    rooms["center_1"].gates.bottom = false;
                }
                if(currentRoomKey === "south_4"){
                    room.gates.top = false;
                }
                room.chests = false
                buildRoom();                
            }
        }   
    } else {
        for (let ch of chests){
            context.drawImage(
                chestSprite,
                0, 0,
                48, 32,
                ch.x, ch.y,
                ch.width, ch.height
            );

            if (is_colliding({x: p.x + p.xChange, y: p.y, size: p.size}, ch)){
                canMoveRight = false;
            } 
            if (is_colliding({x: p.x - p.xChange, y: p.y, size: p.size}, ch)){
                canMoveLeft = false;
            } 
            if (is_colliding({x: p.x, y: p.y - p.yChange, size: p.size}, ch)){
                canMoveUp = false;
            } 
            if (is_colliding({x: p.x, y: p.y + p.yChange, size: p.size}, ch)){
                canMoveDown = false;
            } 
        }

        if (enemies.length === 0) {
            room.cleared = true;
            buildRoom();
        }
    }

    updateEnemies();
    updateBullets();
    updatePlayerBullets();

    if (PlayerInvincibility === 0) {
        for (let enemy of enemies) {
            if (is_colliding(p, enemy)) {
                playerHp -= (enemy.damage);
                PlayerInvincibility = 30;
                if (playerHp <= 0) {
                    stop(2);
                    return;
                }
                break;
            }
        }
    }

    drawEnemies();
    drawBullets();
    drawPlayerBullets();

    if (moveRight && canMoveRight) p.x += p.xChange;
    if (moveLeft && canMoveLeft) p.x -= p.xChange;
    if (moveUp && canMoveUp) p.y -= p.yChange;
    if (moveDown && canMoveDown) p.y += p.yChange;

    checkRoomTransition();

    context.fillStyle = "grey";
    for (let wall of walls) {
        context.fillRect(wall.x, wall.y, wall.width, wall.height);
    }
    
    context.fillStyle = "red";
    for (let gate of gates){
        context.fillRect(gate.x, gate.y, gate.width, gate.height);
    }
    
    context.fillStyle = "white";
    context.fillRect(p.x, p.y, p.size, p.size);
    
    drawTimer();
    drawPlayerHealth();

    if (rooms["south_4"].chests === false){
        stop(1);
        return;
    }

}

function is_colliding(obj1, obj2) {
    let obj1Width = obj1.width || obj1.size;
    let obj1Height = obj1.height || obj1.size;
    let obj2Width = obj2.width || obj2.size;
    let obj2Height = obj2.height || obj2.size;

    return !(obj1.x + obj1Width <= obj2.x || obj1.x >= obj2.x + obj2Width ||
             obj1.y + obj1Height <= obj2.y || obj1.y >= obj2.y + obj2Height);
}

function activate(event) {
    let key = event.key;
    if (event.key ==="ArrowLeft" ||
        event.key === "ArrowRight" ||
        event.key === "ArrowUp" ||
        event.key === "ArrowDown") { 
            event.preventDefault();
    }
    if (key === "ArrowLeft") {
        moveLeft = true;
    } else if (key === "ArrowUp") {
        moveUp = true;
    } else if (key === "ArrowRight") {
         moveRight = true;
    } else if (key === "ArrowDown") {
         moveDown = true;
    }
}

function deactivate(event) {
    let key = event.key;
    if (key === "ArrowLeft") {
        moveLeft = false;
    } else if (key === "ArrowUp") {
        moveUp = false;
    } else if (key === "ArrowRight") {
        moveRight = false;
    } else if (key === "ArrowDown") {
        moveDown = false;
    }
}

function shootBullet(event) {
    let rect = canvas.getBoundingClientRect();
    
    let scaleX = canvas.width / rect.width;
    let scaleY = canvas.height / rect.height;
    let mouseX = (event.clientX - rect.left) * scaleX;
    let mouseY = (event.clientY - rect.top) * scaleY;

    let cx = p.x + p.size / 2;
    let cy = p.y + p.size / 2;
    let dx = mouseX - cx;
    let dy = mouseY - cy;
    let dist = Math.sqrt(dx * dx + dy * dy);
    if (dist === 0) {
        return;
    }

    playerBullets.push({
        x: cx,
        y: cy,
        dx: (dx / dist) * 6,
        dy: (dy / dist) * 6,
        size: 6
    });
}

function drawTimer() {
    let seconds = Math.floor(elapsedTime / 1000);
    context.fillStyle = "white";
    context.font = "16px Arial";
    context.textAlign = "left";
    context.textBaseline = "top";
    context.fillText("Time: " + seconds + "s", 15, 15);
}

function stop(result) {
    window.cancelAnimationFrame(request);
    window.removeEventListener("keydown", activate);
    window.removeEventListener("keyup", deactivate);
    canvas.removeEventListener("mousedown", shootBullet);

    if (result === 1) {
        document.getElementById("win-hp").textContent = "You finished with " + playerHp + " / " + maxPlayerHp + " HP";
        document.getElementById("hp-input").value = playerHp;
        document.getElementById("time-input").value = Math.round(elapsedTime / 1000);
        document.getElementById("win-form").style.display = "block";
    } else if (result === 2) {
        document.getElementById("lose-form").style.display = "block";
    }
}