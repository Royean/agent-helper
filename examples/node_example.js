/**
 * Agent Helper Node.js 调用示例
 *
 * 安装依赖: npm install axios
 */

const axios = require('axios');

// ============ 配置 ============
const SERVER_URL = 'http://localhost:8080';
const SERVER_TOKEN = 'ah_server_token_change_in_production';
const DEVICE_ID = 'my-linux-server';

// 创建 axios 实例
const api = axios.create({
    baseURL: SERVER_URL,
    headers: {
        'Authorization': `Bearer ${SERVER_TOKEN}`,
        'Content-Type': 'application/json'
    },
    timeout: 65000
});

// ============ 封装类 ============

class AgentHelperClient {
    constructor(serverUrl, token, deviceId) {
        this.serverUrl = serverUrl;
        this.token = token;
        this.deviceId = deviceId;
        this.api = axios.create({
            baseURL: serverUrl,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            timeout: 65000
        });
    }

    async send(action, params = {}, reqId = null) {
        const data = {
            device_id: this.deviceId,
            req_id: reqId || this._uuid(),
            action: action,
            params: params
        };

        const resp = await this.api.post('/api/v1/agent/send', data);
        return resp.data;
    }

    async shell(cmd, timeout = 30, cwd = null) {
        const params = { cmd, timeout };
        if (cwd) params.cwd = cwd;
        return await this.send('shell.exec', params);
    }

    async systemInfo() {
        return await this.send('system.info');
    }

    async fileList(path = '/') {
        return await this.send('file.list', { path });
    }

    async fileRead(path, offset = 0, limit = 100000) {
        return await this.send('file.read', { path, offset, limit });
    }

    async fileWrite(path, content, append = false) {
        return await this.send('file.write', { path, content, append });
    }

    async processList() {
        return await this.send('process.list');
    }

    async processKill(pid, signal = 15) {
        return await this.send('process.kill', { pid, signal });
    }

    async service(name, operation = 'status') {
        return await this.send('service.operate', { service: name, operation });
    }

    async listDevices() {
        const resp = await this.api.get('/api/v1/devices');
        return resp.data;
    }

    _uuid() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}

// ============ 使用示例 ============

async function demo() {
    const client = new AgentHelperClient(SERVER_URL, SERVER_TOKEN, DEVICE_ID);

    console.log('='.repeat(50));
    console.log('Agent Helper Node.js 调用示例');
    console.log('='.repeat(50));

    try {
        // 1. 健康检查
        console.log('\n1. 健康检查:');
        const health = await axios.get(`${SERVER_URL}/health`);
        console.log('   状态:', health.data.status);
        console.log('   在线设备:', health.data.connected_devices);

        // 2. 系统信息
        console.log('\n2. 获取系统信息:');
        const sysInfo = await client.systemInfo();
        if (sysInfo.code === 0) {
            const data = sysInfo.data.data;
            console.log('   主机名:', data.hostname);
            console.log('   系统:', data.system, data.release);
            console.log('   架构:', data.machine);
            console.log('   运行时间:', data.uptime);
        }

        // 3. 执行命令
        console.log('\n3. 执行命令 (whoami):');
        const whoami = await client.shell('whoami');
        if (whoami.code === 0) {
            console.log('   输出:', whoami.data.stdout?.trim());
        }

        // 4. 磁盘空间
        console.log('\n4. 查看磁盘空间:');
        const df = await client.shell('df -h / | tail -1');
        if (df.code === 0) {
            console.log('   ', df.data.stdout?.trim());
        }

        // 5. 进程列表
        console.log('\n5. 进程列表 (前3个):');
        const procs = await client.processList();
        if (procs.code === 0) {
            const processes = procs.data.data.processes.slice(0, 3);
            for (const proc of processes) {
                console.log(`   PID ${proc.pid}: ${proc.command.substring(0, 50)}...`);
            }
        }

        // 6. 服务状态
        console.log('\n6. 服务状态 (sshd):');
        const service = await client.service('sshd', 'is-active');
        if (service.code === 0) {
            console.log('   状态:', service.data.stdout?.trim());
        }

        // 7. 在线设备
        console.log('\n7. 在线设备:');
        const devices = await client.listDevices();
        if (devices.code === 0) {
            console.log('   共', devices.devices.length, '个设备在线');
            for (const device of devices.devices) {
                console.log('   -', device.device_id);
            }
        }

    } catch (error) {
        console.error('错误:', error.message);
        if (error.response) {
            console.error('响应:', error.response.data);
        }
    }

    console.log('\n' + '='.repeat(50));
    console.log('示例完成');
    console.log('='.repeat(50));
}

// 运行
demo();
