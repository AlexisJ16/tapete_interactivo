// Coste computacional del nucleo: cuanto cuesta procesar un tick y una pisada.
// Mide GameEngine puro (sin ctypes, sin E/S), serializando cada evento como hace
// el firmware y descartando el resultado.
//
// NO es la latencia del lazo fisico pisada->LED: eso exige el prototipo instrumentado.
//
//   g++ -std=c++17 -O2 -I firmware/lib/GameCore scripts/bench_nucleo.cpp \
//       firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp -o build/bench_nucleo
#include <chrono>
#include <cstdio>

#include "GameEngine.h"

namespace {

// Hardware virtual: reloj inyectado, salidas inertes (como el puente del simulador).
class HardwareFalso : public IHardware {
public:
    uint32_t millis() override { return ms_; }
    int leerSensor(int) override { return 0; }
    void setLed(int, int) override {}
    void reproducirSonido(int) override {}
    void avanzar(uint32_t ms) { ms_ = ms; }

private:
    uint32_t ms_ = 0;
};

volatile size_t sumidero = 0;

// Estado observado por el emisor: que casilla esta encendida y si la sesion acabo.
struct Observador {
    int encendida = 0;
    bool finished = false;
};

using Reloj = std::chrono::steady_clock;

double ns_por_llamada(const Reloj::time_point& t0, const Reloj::time_point& t1, long n) {
    return std::chrono::duration<double, std::nano>(t1 - t0).count() / static_cast<double>(n);
}

// Tick en RUNNING sin transiciones: el coste del bucle principal del firmware.
void bench_tick(long n) {
    HardwareFalso hw;
    Observador obs;
    GameEngine motor(hw, [&obs](const proto::Evento& e) { sumidero += e.serializar().size(); (void)obs; });
    motor.procesarLinea("{\"cmd\":\"set_seed\",\"seed\":777}");
    motor.procesarLinea("{\"cmd\":\"set_mode\",\"mode\":2,\"level\":1}");
    motor.procesarLinea("{\"cmd\":\"start\"}");

    const auto t0 = Reloj::now();
    for (long i = 0; i < n; ++i) {
        hw.avanzar(static_cast<uint32_t>(i % 500));  // nunca agota la ventana (3000 ms)
        motor.actualizar();
    }
    const auto t1 = Reloj::now();
    std::printf("%-34s %8.1f ns/llamada  (%ld ticks)\n", "actualizar() [tick en RUNNING]",
                ns_por_llamada(t0, t1, n), n);
}

// Sesiones completas jugadas con acierto: cada pisada SI produce eventos (led, sound,
// score y, al cerrar la ventana del recomendador, suggest).
void bench_sesion(long sesiones) {
    HardwareFalso hw;
    Observador obs;
    GameEngine motor(hw, [&obs](const proto::Evento& e) {
        sumidero += e.serializar().size();
        if (e.tipo == proto::Evento::Tipo::LED && e.level > 0) obs.encendida = e.cell;
        if (e.tipo == proto::Evento::Tipo::STATE && e.status == "finished") obs.finished = true;
    });

    long pisadas = 0;
    uint32_t ms = 0;
    const auto t0 = Reloj::now();
    for (long s = 0; s < sesiones; ++s) {
        obs = Observador{};
        motor.procesarLinea("{\"cmd\":\"set_seed\",\"seed\":777}");
        motor.procesarLinea("{\"cmd\":\"set_mode\",\"mode\":2,\"level\":4}");  // 12 rondas
        motor.procesarLinea("{\"cmd\":\"start\"}");
        while (!obs.finished && obs.encendida != 0) {
            ms += 10;
            hw.avanzar(ms);
            motor.actualizar();
            const int objetivo = obs.encendida;
            obs.encendida = 0;
            motor.pisar(objetivo);
            ++pisadas;
        }
    }
    const auto t1 = Reloj::now();
    const double total_ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    std::printf("%-34s %8.1f ns/pisada    (%ld pisadas efectivas)\n",
                "pisar() [pisada que emite eventos]", total_ns / static_cast<double>(pisadas), pisadas);
    std::printf("%-34s %8.2f us/sesion    (%ld sesiones de 12 rondas)\n",
                "sesion completa (nivel 4)", total_ns / 1000.0 / static_cast<double>(sesiones), sesiones);
}

}  // namespace

int main() {
    bench_tick(1000000);
    bench_sesion(20000);
    return 0;
}
